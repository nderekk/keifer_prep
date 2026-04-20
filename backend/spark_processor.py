from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, expr
from pyspark.sql.types import StructType, StructField, StringType, LongType

# 1. Start Spark with the Kafka connector package
spark = SparkSession.builder \
    .appName("GreekPoliticsClassifier") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.13:4.1.1") \
    .getOrCreate()
    
# Set logging level to avoid too much "INFO" noise in the console
spark.sparkContext.setLogLevel("WARN")

# 2. Define the schema based on your Greek article JSON
schema = StructType([
    StructField("source", StringType(), True),
    StructField("url", StringType(), True),
    StructField("title", StringType(), True),
    StructField("date", LongType(), True),
    StructField("text", StringType(), True)
])

# 3. Connect to Kafka
raw_stream = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "raw-articles") \
    .option("startingOffsets", "earliest") \
    .load()

# 4. Transform: Binary -> String -> JSON -> Columns
# We use 'utf-8' specifically for Greek character support
parsed_stream = raw_stream.selectExpr("CAST(value AS STRING) as json_payload") \
    .select(from_json(col("json_payload"), schema).alias("article")) \
    .select("article.*")

# 5. (Draft) Political Classification Logic
# This is where your model goes. For now, we'll just check if the text mentions 'Τραμπ'
classified_stream = parsed_stream.withColumn(
    "political_focus", 
    expr("CASE WHEN text LIKE '%Τραμπ%' THEN 'International/US' ELSE 'General' END")
)

# 6. Output to Console
query = classified_stream.writeStream \
    .outputMode("append") \
    .format("console") \
    .option("truncate", "false") \
    .start()

print("🚀 Spark is listening! Send data via producer.py to see it here...")
query.awaitTermination()