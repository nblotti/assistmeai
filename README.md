

               ###     ######   ######  ####  ######  ######## ##     ## ########    ###    ####
              ## ##   ##    ## ##    ##  ##  ##    ##    ##    ###   ### ##         ## ##    ## 
             ##   ##  ##       ##        ##  ##          ##    #### #### ##        ##   ##   ## 
            ##     ##  ######   ######   ##   ######     ##    ## ### ## ######   ##     ##  ## 
            #########       ##       ##  ##        ##    ##    ##     ## ##       #########  ## 
            ##     ## ##    ## ##    ##  ##  ##    ##    ##    ##     ## ##       ##     ##  ## 
            ##     ##  ######   ######  ####  ######     ##    ##     ## ######## ##     ## ####
<p align="right">
  <img src="https://sonarcloud.io/api/project_badges/measure?project=nblotti_assistmeai&metric=alert_status" />
</p>

Welcome to AssistmeAI, the innovative application that lets you engage with customizable AI assistants tailored to your needs.

With AssistmeAI, you can effortlessly chat with AI, accessing personalized assistance around the clock. Upload your documents or search through a curated set of files using natural language to leverage advanced Retrievable Augmented Generation (RAG) for insightful answers. 

Whether you need help drafting a report or retrieving specific information, AssistmeAI ensures you have the right tools at your fingertips, all while respecting your access rights.

Experience the future of intelligent conversations today!

## Architecture
This GitHub repository hosts the backend services of the application, which handle all core functionalities such as interfacing with Large Language Models (LLMs), document management (including embeddings creation) and access control (see <em>Figure 1</em>). Through this backend, all application features can be accessed and tested via the provided APIs. The backend is fully operational and designed to be configured independently, allowing for thorough testing and validation before integrating the frontend.


Exposing all functionalities through REST APIs allows multiple frontends to interact with the backend, ensuring flexibility and scalability. By adhering to this architectural style, diverse clients such as web applications, mobile apps, and third-party services can seamlessly integrate and communicate with the backend services. The key benefits are:

**Flexibility :**
- Multiple Frontends: Different clients can be built independently to interact with the same backend services.
- Device Agnostic: Works across various platforms and devices, from web browsers to mobile applications.

**Scalability :**
- Distributed Architecture: Services can be scaled independently, accommodating growing traffic and functional requirements.
- Load Balancing: REST APIs make it simpler to distribute load across multiple servers.
 
**Maintainability :**
- Loose Coupling: Frontend and backend can be maintained and updated independently, enabling teams to work in parallel.
- Standardization: REST API conventions promote a standardized method of communication, easing the learning curve for developers.

 
For a practical example of a frontend that interacts with such REST APIs, please check  <a href="https://github.com/nblotti/simple_front">this repository </a>. on GitHub.


<p align="center">
 <img src="https://github.com/nblotti/assistmeai/blob/master/Assistme.jpg?raw=true" width="60%"/>
    <br>
    <em>Figure 1 : Architecture</em>
</p>

## Database support

The application is designed to use PostgreSQL because it supports standard SQL databases and advanced features such as embedding through the <a href="https://github.com/pgvector/pgvector">PGVector extension<a>, but it can be easily adapted to use any other kind of database. 

The creation of the tables is managed by using a provided [sql script](create_tables_postgres.sql)

## DockerFile, Kubernetes Deployment, and Service Files
For the seamless deployment and management of the application, we have included the necessary configuration files:

**DockerFile:**

- A reference [Dockerfile](Dockerfile) file is provided. It contains the instructions to build the Docker image for the application. It specifies the base image, dependencies, configuration settings, and the commands to run the application.
- Adapt it to customize your need 

**Kubernetes (k8s) Deployment File:**

- A reference [K8s deployment file](assistmeai_deployment.yaml) file is provided. It specifies details like the number of replicas (instances) of the application, the Docker image to use, resource requests and limits, environment variables, and more.
- Once you have built your Docker container and pushed it to your favorite repository (like DockerHub), you will need to make modifications to the script to update the image name and registry credentials (regcreds)

**Kubernetes (k8s) Service File:**

- A reference [K8s service file](assistmeai-service.yaml) file is provided.It defines the Kubernetes Service, which is responsible for exposing the application to external traffic or internal communication within the cluster.
- The application is initially configured to run behind a reverse proxy and not exposed externally. Depending on your requirements, you can easily adapt the exposure by modifying the service's port type.

By using these files, you can easily build the Docker image, deploy the application on a Kubernetes cluster, and expose it for access. Detailed instructions and configurations are specified within the files to ensure a smooth setup and operation.


## QuickStart

**Check out the code**
```
git clone https://github.com/nblotti/assistmeai.git

#Navigate into the project directory:

cd <project-directory>
```
**Configure Docker network, create the database and run the scripts**

- Create a docker network to allow intercontainer communication
```
docker network create my_network
```
- A postgres docker image is provided for the tests run it :
```
docker build -f PGDockerfile -t some-postgres .
docker run --name some-postgres --network my_network -e POSTGRES_PASSWORD=mysecretpassword -p 5432:5432 -d some-postgres
```


- Create the database and run the initialization scripts

```
# Set variables
DB_PASSWORD="mysecretpassword"
DB_HOST="localhost"
DB_USER="postgres"
DB_NAME="rag"

# Create the database
PGPASSWORD=$DB_PASSWORD createdb -h $DB_HOST -U $DB_USER $DB_NAME

# Run the SQL script
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f create_tables_postgres.sql
```

**Adapt the config file**

- Adapt the  and set the required variables. The first part is related to the database (note that for tests, the same database will contains files, data and embeddings, but that it can be easily splitted). The second part is related to the models available for the assstant functionnality.

- To adapt the [config file](config.py), first set the required database variables, including host, port, dbname, user, and password, keeping in mind that the same database will handle files, data, and embeddings for testing purposes. Next, configure the LLM section by specifying the different models available for the assistant functionality, detailing their paths or identifiers as needed.

```

os.environ["DB_NAME"] = "rag"
os.environ["DB_NAME_RAG"] = 'rag'
os.environ["DB_HOST"] = "some-postgres"
os.environ["DB_PORT"] = "5432"
os.environ["DB_USER"] = "postgres"
os.environ["DB_PASSWORD"] = "mysecretpassword"

os.environ["AZURE_OPENAI_API_KEY"] = ""
os.environ["AZURE_OPENAI_ENDPOINT"] = ""
os.environ["AZURE_GPT_35_API_VERSION"] = ""
os.environ["AZURE_GPT_35_CHAT_DEPLOYMENT_NAME"] = ""

os.environ["AZURE_GPT_4_API_VERSION"] = ""
os.environ["AZURE_GPT_4_CHAT_DEPLOYMENT_NAME"] = ""

os.environ["AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT_NAME"] = ""
os.environ["AZURE_OPENAI_EMBEDDINGS_API_VERSION"] = ""

```

- Disable the sslmode in the config file :
```
os.environ[
    "PGVECTOR_CONNECTION_STRING"] = f"postgresql+psycopg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME_RAG')}?sslmode=disable"
```


**Build the docker image and run it**

- Build the image :
```
docker build -t assistmeai-test .
```
- Once the image is built, you can run it with:
```
docker run --network my_network -d -p 8080:8080 --name assistmeai-test -d assistmeai-test
```
**Test it**

- Upload document
```
curl -k -X POST -F "perimeter=1" -F "file=@10_afh_landings.pdf" http://localhost:8080/document/

response -> {"filename":"10_afh_landings.pdf","blob_id":"1"}
```
- Replace pdf_id and pdf_name in the query and create a conversation :
```
curl -X POST http://localhost:8080/conversation/ -H "Content-Type: application/json" -d '{"perimeter":"1","description":"","pdf_id":"1","pdf_name":"10_afh_landings.pdf"}'

response ->{"id":1,"perimeter":"1","description":"","pdf_id":1,"pdf_name":"10_afh_landings.pdf","created_on":"08.08.2024"}
```
- Ask a question on the document (escaping special chars :
```
curl "http://localhost:8080/chat/command/?command=how%20can%20I%20use%20flaps%20while%20landing%3F&conversation_id=1&perimeter=1"

response -> {"result":"You can use flaps while landing to help adjust lift and drag. By extending the flaps during the approach and landing, you can increase lift and lower your approach and landing speeds. This can be beneficial for landing on soft fields or in turbulent conditions. It is important to follow the manufacturer's recommendations for flap settings and airspeeds, as stated in the Airplane Flight Manual or Pilot's Operating Handbook for your specific aircraft. Additionally, it is generally recommended to avoid retracting the flaps during the after-landing roll, as maintaining control of the airplane is a higher priority than flap retraction.","sources":[{"id":"41745124-51ae-4641-9596-267dacd123c3","page":22,"text":"that suddenly affect the airplane at the moment of touchdown. \nFigure 9-24.  Soft/rough field approach and landing. \nThe use of flaps during soft-field landings aids in touching down at minimum speed and is recommended whenever practical. In low-wing airplanes, the flaps may suffer damage from mud, stones, or slush thrown up by the wheels. If flaps are used, it is generally inadvisable to retract them during the after-landing roll because the need for flap retraction is less important than the need for total concentration on maintaining full control of the airplane. \n9-23","blob_id":"1","file_name":"10_afh_landings.pdf","perimeter":"1"},{"id":"4b7eafd9-ded9-402f-9614-7a6a036e2450","page":19,"text":"flaps, the airplane is in a higher pitch attitude. Thus, it requires less of a pitch change to establish the landing attitude and touchdown at a higher airspeed to ensure more positive control. \nPilots often use the normal approach speed plus one-half of the wind gust factors in turbulent conditions. If the normal speed is 70 knots, \nand the wind gusts are 15 knots, an increase of airspeed to 77 knots is appropriate. In any case, the airspeed and the flap setting should conform to airplane manufacturer's recommendations in the AFM/POH. \nUse an adequate amount of power to maintain the proper airspeed and descent path throughout the approach, and retard the throttle to \nidling position only after the main wheels contact the landing surface. Care should be exercised in closing the throttle before the pilot is ready for touchdown. In turbulent conditions, the sudden or premature closing of the throttle may cause a sudden increase in the descent rate, resulting in a hard landing.","blob_id":"1","file_name":"10_afh_landings.pdf","perimeter":"1"},{"id":"28c55a9e-b674-4603-a992-2db60e8fc59d","page":10,"text":"Configuration \nAfter establishing the proper climb attitude and power settings, the pilot's next concern is flap retraction. After the descent has been stopped, the landing flaps are partially retracted or placed in the takeoff position as recommended by the manufacturer. Depending on the airplane’s altitude and airspeed, it is wise to retract the flaps intermittently in small increments to allow time for the airplane to accelerate progressively as they are being raised. A sudden and complete retraction of the flaps could cause a loss of lift resulting in the airplane settling into the ground. [ Figure 9-12] \nFigure 9-12.  Go-around procedure. \n9-11","blob_id":"1","file_name":"10_afh_landings.pdf","perimeter":"1"},{"id":"3355db1b-eb91-4e1c-abfd-f981e8370c2d","page":0,"text":"The manufacturer’s recommended procedures, including airplane configuration and airspeeds, and other information relevant to \napproaches and landings in a specific make and model airplane are contained in the Federal Aviation Administration (FAA)-approved Airplane Flight Manual and/or Pilot’s Operating Handbook (AFM/POH) for that airplane. If any of the information in this chapter differs from the airplane manufacturer’s recommendations as contained in the AFM/POH, the airplane manufacturer’s recommendations take precedence. \nUse of Flaps \nThe following general discussion applies to airplanes equipped with flaps. The pilot may use landing flaps during the descent to adjust lift and drag. Flap settings help determine the landing spot and the descent angle to that spot. [Figure 9-1 and Figure 9-2] Flap extension \nduring approaches and landings provides several advantages by: \n1. Producing greater lift and permitting lower approach and landing speeds,","blob_id":"1","file_name":"10_afh_landings.pdf","perimeter":"1"}]}
```

## Further help
contact nblotti@gmail.com



