from azure.data.tables import TableClient

# Set the connection string and table name
connection_string = "DefaultEndpointsProtocol=https;AccountName=movierecommendations;AccountKey=4BkPpw13lQZIctbbrivxCqfY47bapmaFT6R3kR9zexe+zeXBShRU+Q8oQsVKiApkb90AdpMmdsbd+AStzQPERA==;EndpointSuffix=core.windows.net"
table_name = "logs"

# Create the TableClient object
table_client = TableClient.from_connection_string(connection_string, table_name)

# Function to insert an entity into the table
def insert_entity(partition_key, row_key, **properties):
    entity = {"PartitionKey": partition_key, "RowKey": row_key}
    entity.update(properties)
    table_client.create_entity(entity)

# Function to query entities from the table
def query_entities(filter_expression=None):
    entities = []
    query_results = table_client.query_entities(filter_expression)
    for entity in query_results:
        entities.append(entity)
    return entities

# Usage example
#insert_entity("partition_key", "row_key", Name="John Doe", Age=30)
results = query_entities("Name eq 'John Doe'")
for entity in results:
    print(entity)