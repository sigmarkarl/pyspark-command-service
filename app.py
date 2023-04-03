import subprocess
import logging
import json
from flask import Flask, request
from pyspark.sql import SparkSession
from kubernetes import client, config

app = Flask(__name__)
spark = SparkSession.builder.appName(__name__).getOrCreate()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
logger.addHandler(handler)


@app.route('/', methods=['POST'])
def submit_command():
    logger.info('Received request on /')
    try:
        content = request.data.decode('utf-8')
        json_data = json.loads(content)
        code_type = json_data['type']
        if code_type == 'SQL':
            sql = json_data['code']
            df = spark.sql(sql)
            result = json_data['result_type']
            if result == 'table':
                return df.toPandas().to_html()
            elif result == 'json':
                return df.toPandas().to_json(orient='records')
            elif result == 'csv':
                return df.toPandas().to_csv()
            elif result == 'text':
                return df.toPandas().to_string()
            elif result == 'count':
                return str(df.count())
            elif result == 'url':
                url = json_data['result_url']
                if url.endswith('.csv'):
                    df.write.csv(url)
                elif url.endswith('.json'):
                    df.write.json(url)
                elif url.endswith('.parquet'):
                    df.write.parquet(url)
                elif url.endswith('.orc'):
                    df.write.orc(url)
                return 'Success'
            else:
                return 'Invalid result type'
        elif code_type == 'Python':
            code = json_data['code']
            return exec(code)
        elif code_type == 'R':
            code = json_data['code']
            subprocess.run(['Rscript', '-e', code])
        else:
            return 'Invalid type'
    except Exception as e:
        return f'Error {e}'


def load_kubernetes():
    config.load_incluster_config()
    api = client.CoreV1Api()
    return api


def start_jupyter():
    api_instance = load_kubernetes()
    pod_name = open("/var/run/secrets/kubernetes.io/serviceaccount/pod.name").read()
    namespace = open("/var/run/secrets/kubernetes.io/serviceaccount/namespace").read()
    pod = api_instance.read_namespaced_pod(name=pod_name.strip(), namespace=namespace.strip())
    cluster_id = pod.labels['bigdata.spot.io/cluster-id']
    app_id = pod.labels['spark-app-name']
    subprocess.run(['jupyter-server',
                    '--no-browser',
                    '--port=8888',
                    '--ip=0.0.0.0',
                    '--ServerApp.allow_origin=*',
                    '--ServerApp.port_retries=0',
                    '--ServerApp.token=""',
                    '--NotebookApp.disable_check_xsrf=True',
                    f'--NotebookApp.base_url=/api/open/spark/cluster/{cluster_id}/app/{app_id}/notebook'])


if __name__ == '__main__':
    start_jupyter()
    app.run(debug=True, host='0.0.0.0', port=5002)
