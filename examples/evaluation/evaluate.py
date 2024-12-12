from time import sleep

import mixedvoices as mv
from tinkerers.agent import DentalAssistant, conversation_ended

project = mv.load_project("dental_clinic")
version = project.load_version("v1")
evaluator = version.create_evaluator()


for i, eval_case in enumerate(evaluator):
    text_assistant = DentalAssistant(mode="text")
    conversation = text_assistant.conversation_loop()
    next(conversation)
    assistant_message = ""
    print("----------------")
    print("Starting test case", i)
    print("Evaluator Prompt: ", eval_case.prompt)
    while 1:
        if conversation_ended(assistant_message):
            scores = eval_case.respond(assistant_message, end=True)
            print(scores)
            break
        evaluator_message = eval_case.respond(assistant_message)
        _, assistant_message = conversation.send(evaluator_message)
        print(f"Evaluator: {evaluator_message}")
        print(f"Assistant: {assistant_message}\n")

    sleep(5)
