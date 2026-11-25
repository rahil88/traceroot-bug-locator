from dotenv import load_dotenv
load_dotenv()

import traceroot
from traceroot import Integration, observe
from openai import OpenAI

traceroot.initialize(integrations=[Integration.OPENAI])
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

@observe(name="first-trace", type="agent")
def ask(question):
    r = client.chat.completions.create(
        model="qwen2.5-3b-16k", temperature=0,
        messages=[{"role": "user", "content": question}])
    return r.choices[0].message.content

print(ask("Say hello in five words."))
traceroot.flush()