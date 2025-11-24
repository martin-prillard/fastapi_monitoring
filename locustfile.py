from locust import HttpUser, task, between
import random

class FastAPIUser(HttpUser):
    """
    Classe Locust pour tester l'API FastAPI avec des scénarios de charge.
    """
    wait_time = between(1, 3)  # Attente entre 1 et 3 secondes entre les requêtes
    
    def on_start(self):
        """Exécuté une fois au démarrage de chaque utilisateur virtuel"""
        # Test de santé pour vérifier que l'API est accessible
        self.client.get("/")
    
    @task(3)
    def predict_iris(self):
        """
        Test de l'endpoint /predict avec des données Iris aléatoires.
        Poids 3 : cette tâche sera exécutée 3 fois plus souvent que les autres.
        """
        # Génération de données Iris réalistes
        data = {
            "sepal_length": round(random.uniform(4.0, 8.0), 1),
            "sepal_width": round(random.uniform(2.0, 4.5), 1),
            "petal_length": round(random.uniform(1.0, 7.0), 1),
            "petal_width": round(random.uniform(0.1, 2.5), 1)
        }
        
        with self.client.post(
            "/predict",
            json=data,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(1)
    def health_check(self):
        """
        Test de l'endpoint de santé.
        Poids 1 : exécuté moins fréquemment que predict.
        """
        self.client.get("/")
    
    @task(1)
    def get_metrics(self):
        """
        Test de l'endpoint /metrics pour vérifier les métriques Prometheus.
        Poids 1 : exécuté moins fréquemment.
        """
        self.client.get("/metrics")

