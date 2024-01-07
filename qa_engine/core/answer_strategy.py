import os

os.environ["TOKENIZERS_PARALLELISM"] = "false"  # Something for tokenizers library, must be here

from abc import ABC, abstractmethod
from qa_engine.core.models import TextEntry
# from transformers import pipeline
import openai


class AnswerStrategy(ABC):

    @abstractmethod
    def formulate_answer(self, query: str, entries: [TextEntry], *args, **kwargs) -> str:
        pass


class OpenAIAnswerStrategy(AnswerStrategy):

    def __init__(self, model_name, openai_key, organization):
        self.model_name = model_name
        openai.api_key = openai_key
        openai.organization = organization

    def openai_completion(self, text: str) -> str:
        response = openai.Completion.create(
            engine=self.model_name,
            prompt=text,
            temperature=0.5,
            max_tokens=10000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        openai_response = response.choices[0].text.strip()

        return openai_response

    def openai_chat_completion(self, text: str) -> str:
        response = openai.ChatCompletion.create(
            model=self.model_name,
            temperature=0.5,
            max_tokens=512,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            messages=[
                {"role": "system", "content": ""},
                {"role": "user", "content": text},
            ]
        )
        openai_response = response['choices'][0]['message']['content'].strip()
        return openai_response

    def formulate_answer(self, query: str, entries: [TextEntry], *args, **kwargs) -> str:
        lines = [
            "Result from Google Search:",
            "\n".join(entry.text for entry in entries),
            f"Question: {query}",
            "Answer: "
        ]
        # print(f"Lines: {lines}")
        if self.model_name.startswith("text"):
            response = self.openai_completion("\n".join(lines))
        else:
            response = self.openai_chat_completion("\n".join(lines))

        return response


# class SentenceTransformerAnswerStrategy(AnswerStrategy):
#
#     def __init__(self, model_name: str):
#         self.model_name = model_name
#
#     def formulate_answer(self, query: str, entries: [TextEntry], *args, **kwargs) -> str:
#         # take first top 5 entries
#         entries = entries[:5]
#         generator = pipeline('text-generation', model=self.model_name)
#         text = "Context:\n\n"
#         for entry in entries:
#             text += f"{entry.text}\n\n"
#         text += f"Question: {query}\n\n"
#         text += "Given the context, the answer is"
#         generated_text = generator(text, max_new_tokens=64)
#         full_text = generated_text[0]['generated_text']
#         answer = full_text.split("Given the context, the answer is")[1]
#         return answer


