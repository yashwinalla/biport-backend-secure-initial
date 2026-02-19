from app.core.config import OpenAIConfig, AzureOpenAIConfig
from openai import APIConnectionError, AuthenticationError
from app.core.logger_setup import logger
import os


cloud_provider = os.getenv("CLOUD_PROVIDER", "aws").lower().strip()
if cloud_provider == "azure":
    openai_config = AzureOpenAIConfig()
    client = openai_config.get_openai_client()
    is_azure = True
else:
    openai_config = OpenAIConfig()
    client = openai_config.get_openai_client()
    is_azure = False

def gpt_model(model, system_message, user_message, response_format):
    try:
        if is_azure:
            model_or_deployment = openai_config.deployment_name
        else:
            model_or_deployment = model if model else openai_config.model_name
        response = client.chat.completions.create(
            model = model_or_deployment,
            messages=[
                {
                    "role" : "system",
                    "content" : [
                            {
                            "type": "text",
                            "text": system_message
                            }
                        ]
                },
                {
                    "role" : "user",
                    "content" : [
                            {
                            "type": "text",
                            "text": user_message
                            }
                        ]
                }
            ],
            response_format={
                "type": response_format
            }
        )

        return response.choices[0].message.content
    except APIConnectionError as e:
        logger.error(f"Issue in connecting to OpenAI API: {str(e)}")
        raise ValueError('Issue in connecting to OpenAI API')
    except AuthenticationError as e:
        logger.error(f"OpenAI key or token was invalid, expired, or revoked.: {str(e)}")
        raise ValueError('OpenAI key or token was invalid, expired, or revoked.')  
