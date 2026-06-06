# Docs
## Use LLM Chat

Your application, when deployed, has an environment variable called `SERVER_URL`, which points to the backend that mediates with Watsonx. To use the chat endpoint,
construct the URL as follows `${SERVER_URL}/api/llm/chat` and follow the following
instructions:

- Set the `Content-Type` header to `application/json`
- Set the `Authorization` header to `Bearer ${SERVER_TOKEN}`
- Use a HTTP POST
- Construct the payload based on the following example

```json
{
    "messages": [
        {
            "role": "user",
            "content": "<prompt>"
        }
    ]
}
```

The role can be `user`, `system`, or `assistant`. You will then receive a response as follows:

```json
{
    "response": "Answer"
}
```

Please also note:
- Since we only have a limited number of tokens available, please be mindful of the other participants.
- We use Granite 4 Small in the background.
- The context size is fairly small (~1024 tokens).