from diagrams import Diagram, Cluster
from diagrams.gcp.analytics import PubSub
from diagrams.gcp.compute import Functions
from diagrams.gcp.devtools import Scheduler
from diagrams.custom import Custom

with Diagram("Architecture", show=False, direction="LR"):
    notion = Custom("Notion", "./icon/notion_icon.png")
    with Cluster("GCP"):
        google_fit = Custom("Google Fit", "./icon/google_fit_icon.png")
        scheduler = Scheduler("Cloud Scheduler")
        pubsub = PubSub("Pub/Sub")
        functions = Functions("Cloud Functions")

    scheduler >> pubsub >> functions
    google_fit >> functions
    functions >> notion

