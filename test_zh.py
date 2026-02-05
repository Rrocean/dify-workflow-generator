from dify_workflow.interactive import InteractiveBuilder

builder = InteractiveBuilder(lang='zh')
print(builder.start_message())
print()
print('--- Processing answers ---')
builder.process_answer('翻译助手')
print(f'Name: {builder.intent.name}')
builder.process_answer('将文本翻译成指定语言')
print(f'Desc: {builder.intent.description}')
builder.process_answer('1')
print(f'Mode: {builder.intent.mode}')
builder.process_answer('文本, 目标语言')
print(f'Inputs: {[v["name"] for v in builder.intent.input_variables]}')
