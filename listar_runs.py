import os
os.environ['MLFLOW_ALLOW_FILE_STORE'] = 'true'
import mlflow

mlflow.set_tracking_uri('file:///D:/Trabalho/Ciência de Dados/Material/Projetos III/NorthData-Consulting-Classific-ESG-por-Machine-Learning/mlruns')
client = mlflow.tracking.MlflowClient()

for exp in client.search_experiments():
    print(f'Experimento: {exp.name} | ID: {exp.experiment_id}')
    runs = client.search_runs(exp.experiment_id)
    for r in runs:
        print(f'  run_id: {r.info.run_id}')
        print(f'  nome:   {r.data.tags.get("mlflow.runName", "")}')
        print(f'  metricas: {r.data.metrics}')
        print()