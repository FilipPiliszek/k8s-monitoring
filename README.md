# 🚀 Monitoring zasobów Kubernetes

Witaj w repozytorium projektu skupiającego się na monitorowaniu i optymalizacji zasobów (CPU/RAM) w klastrze Kubernetes. Głównym celem projektu jest zbudowanie zautomatyzowanego narzędzia w Pythonie do agregacji metryk. Repozytorium zawiera przygotowane przez nas pełne środowisko testowe, autorską aplikację obciążeniową oraz konfigurację monitoringu.

## 🛠 Wykorzystane technologie
* **Infrastruktura:** Minikube, Docker
* **Orkiestracja:** Kubernetes (K8s)
* **Zarządzanie pakietami:** Helm
* **Monitoring:** Prometheus, Grafana, PromQL
* **Aplikacja testowa:** Python (Flask)

## 📁 Struktura repozytorium
* `stress_test_app/` - Kod źródłowy aplikacji w Pythonie (Flask) generującej sztuczne obciążenie CPU/RAM w trybach Step i Peak, wraz z plikiem Dockerfile.
* `helm_charts/` - Własny Helm Chart do zautomatyzowanego wdrażania aplikacji testowej na klaster.
* `grafana/` - Gotowy do importu dashboard Grafany (`stress-test-dashboard.json`) z panelami CPU/RAM, liniami limitów (200m / 128Mi) oraz licznikiem restartów (OOMKilled).
* `docs/` - Notatki, logi oraz zrzuty ekranu z wyłapanych incydentów (wykresy z Grafany).

## 📊 Opis środowiska i przeprowadzonych testów

### 1. Przygotowanie monitoringu
Środowisko wykorzystuje pełny stos `kube-prometheus-stack` wdrażany za pomocą menedżera pakietów Helm. Zapewnia to natychmiastową i bezbłędną konfigurację połączenia między bazą Prometheus a narzędziem do wizualizacji (Grafana), a także automatyczne zbieranie metryk systemowych węzła.

### 2. Aplikacja obciążeniowa (Stress Test)
Aby móc przetestować narzędzia wyłapujące zużycie zasobów, stworzyliśmy autorski obraz Dockerowy z prostą aplikacją. Aplikacja wystawia dedykowane endpointy (adresy URL), które po wywołaniu celowo zapętlają procesor lub alokują duże ilości pustych danych w pamięci RAM. Aplikacja jest zamykana w obraz i wdrażana na lokalny klaster za pomocą naszego Helm Charta.

### 3. Generowanie i wyłapywanie incydentów
Dzięki powiązaniu aplikacji z monitoringiem jesteśmy w stanie wygenerować sztuczny incydent (skok zużycia zasobów aplikacji), a następnie skutecznie go wyłapać i zwizualizować. W tym celu zamiast generycznych dashboardów korzystamy z bezpośrednich zapytań w języku PromQL (np. wykorzystując metryki `container_cpu_usage_seconds_total` oraz `container_memory_working_set_bytes`), co pozwala na precyzyjną weryfikację anomalii w panelu Grafany.

## ⚙️ Jak uruchomić projekt lokalnie?

### 1. Uruchomienie klastra i monitoringu
Upewnij się, że masz włączonego Docker Desktop, a następnie otwórz terminal (PowerShell) i uruchom klaster:
```powershell
minikube start
kubectl create namespace monitoring
```
Zainstaluj stos Prometheusa z Grafaną (ustawiamy hasło do Grafany na admin):
```powershell
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install my-prometheus prometheus-community/kube-prometheus-stack --namespace monitoring --set grafana.adminPassword=admin
```
### 2. Budowa i wdrożenie aplikacji obciążeniowej
Obraz budujemy bezpośrednio w wewnętrznym magazynie obrazów Minikube. Używamy `minikube image build` (a nie `docker build`), bo na Windows z Docker Desktop `docker build` potrafi zbudować obraz w Docker Desktop zamiast w Minikube:
```powershell
minikube image build -t test:1.0.1 ./stress_test_app
```
Wdrażamy aplikację na klaster za pomocą naszego Helm Charta:
```powershell
cd ../helm_charts/stress-test
helm install test-app .
```
> Po każdej zmianie kodu w `app.py`: przebuduj obraz (`minikube image build -t test:1.0.1 ./stress_test_app`) i wymuś nowy pod komendą `kubectl rollout restart statefulset test-app-stress-test` (tag się nie zmienia, więc sam Helm poda nie odświeży).
### 3. Uruchomienie tuneli i testy
Aby dostać się do interfejsów z poziomu przeglądarki (localhost), uruchom dwa tunele w osobnych oknach terminala:
```powershell
# Otwarcie Grafany (dostęp pod: http://localhost:3000)
kubectl port-forward svc/my-prometheus-grafana -n monitoring 3000:80

# Otwarcie aplikacji testowej (dostęp pod: http://localhost:8080)
kubectl port-forward svc/test-app-stress-test 8080:8080
```
Aplikacja udostępnia trzy testy: RAM w trybie Step (schodkowy) i Peak (nagły skok) oraz CPU w trybie Peak:

| Endpoint | Tryb | Opis |
|---|---|---|
| `http://localhost:8080/cpu/peak` | Peak Test | Natychmiastowe pełne obciążenie CPU |
| `http://localhost:8080/ram/step` | Step Test | Stopniowa alokacja małych porcji RAM |
| `http://localhost:8080/ram/peak` | Peak Test | Jednorazowa alokacja dużego bloku RAM |

Parametry (przekazywane w URL jako query string, wszystkie opcjonalne):

| Endpoint | Parametr | Domyślnie | Znaczenie |
|---|---|---|---|
| `/cpu/peak` | `seconds` | `15` | Jak długo (s) trzymać pełne obciążenie CPU |
| `/ram/step` | `chunks` | `15` | Liczba porcji pamięci do zaalokowania (co 2 s) |
| `/ram/step` | `mb` | `5` | Rozmiar pojedynczej porcji w MB |
| `/ram/peak` | `mb` | `80` | Rozmiar jednorazowo alokowanego bloku w MB |

Przykłady wywołań:
```text
# CPU – ostry, długi skok na 30 s
http://localhost:8080/cpu/peak?seconds=30

# RAM – schodek: 20 porcji po 4 MB (łącznie ~80 MB)
http://localhost:8080/ram/step?chunks=20&mb=4

# RAM – widoczny peak tuż pod limitem 128Mi (baza ~22 MB + 100 MB = ~122 MB)
http://localhost:8080/ram/peak?mb=100

# RAM – celowe przekroczenie limitu -> OOMKilled (demo incydentu)
http://localhost:8080/ram/peak?mb=150
```
> Uwaga RAM: limit kontenera to 128Mi (~134 MB), a sama aplikacja zajmuje ~22 MB. Wartości `mb` powyżej ~110 dla `/ram/peak` przekroczą limit i pod zostanie ubity (`OOMKilled`).

Po wywołaniu wybranego adresu obserwuj skoki na wykresach w Grafanie.
