def lambda_handler(event, context):
    print("Log: Hello From Lambda")
    print(f"event={event}")

    return {
        "statusCode":200,
        "body" : "Hello World"
    }