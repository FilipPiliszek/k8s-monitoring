# 🚀 Monitoring zasobów Kubernetes

Witaj w repozytorium projektu skupiającego się na monitorowaniu i optymalizacji zasobów (CPU/RAM) w klastrze Kubernetes. Głównym celem projektu jest zbudowanie zautomatyzowanego narzędzia w Pythonie do agregacji metryk. Repozytorium zawiera przygotowane przez nas pełne środowisko testowe, autorską aplikację obciążeniową oraz konfigurację monitoringu.

## 🛠 Wykorzystane technologie
* **Infrastruktura:** Minikube, Docker
* **Orkiestracja:** Kubernetes (K8s)
* **Zarządzanie pakietami:** Helm
* **Monitoring:** Prometheus, Grafana, PromQL
* **Aplikacja testowa:** Python (Flask)

## 📁 Struktura repozytorium
* `stress_test_app/` - Kod źródłowy aplikacji w Pythonie (służącej do generowania sztucznego obciążenia CPU/RAM) oraz jej plik Dockerfile.
* `helm_charts/` - Własny Helm Chart stworzony w celu zautomatyzowanego wdrażania naszej aplikacji testowej na klaster.
* `scripts/` - Narzędzie w Pythonie łączące się z API Prometheusa do analizy i raportowania optymalizacji zasobów (w trakcie tworzenia).
* `docs/` - Notatki ze spotkań, logi oraz zrzuty ekranu z wyłapanych incydentów (np. wykresy z Grafany).

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
Aby Minikube widział nasz obraz, musimy go zbudować bezpośrednio w jego wewnętrznym środowisku Dockerowym:
```powershell
# Aktywacja Dockera w Minikubie
minikube docker-env | Invoke-Expression

# Budowa obrazu
cd stress_test_app
docker build -t test:1.0.0 .
```
Wdrażamy aplikację na klaster za pomocą naszego Helm Charta:
```powershell
cd ../helm_charts/stress-test
helm install test-app .
```
### 3. Uruchomienie tuneli i testy
Aby dostać się do interfejsów z poziomu przeglądarki (localhost), uruchom dwa tunele w osobnych oknach terminala:
```powershell
# Otwarcie Grafany (dostęp pod: http://localhost:3000)
kubectl port-forward svc/my-prometheus-grafana -n monitoring 3000:80

# Otwarcie aplikacji testowej (dostęp pod: http://localhost:8080)
kubectl port-forward svc/test-app-stress-test 8080:8080
```
Po uruchomieniu wejdź w przeglądarce na adres http://localhost:8080/stress-cpu i obserwuj skoki na wykresach w Grafanie.
