from time import sleep

from agent import DentalAssistant, conversation_ended

import mixedvoices as mv

project = mv.load_project("dental_clinic")
version = project.load_version("v1")
evaluator = version.create_evaluation_run()


for i, eval_agent in enumerate(evaluator):
    text_assistant = DentalAssistant(mode="text")
    conversation = text_assistant.conversation_loop()
    next(conversation)
    assistant_message = ""
    print("----------------")
    print("Starting test case", i)
    print("Evaluator Prompt: ", eval_agent.eval_prompt)
    while 1:
        if conversation_ended(assistant_message):
            scores = eval_agent.respond(assistant_message, end=True)
            print(scores)
            break
        evaluator_message = eval_agent.respond(assistant_message)
        _, assistant_message = conversation.send(evaluator_message)
        print(f"Evaluator: {evaluator_message}")
        print(f"Assistant: {assistant_message}\n")

    sleep(5)
