import os
import sys
import signal
import openai
import argparse
from datetime import datetime

def load_config():
    config = {}
    try:
        with open('config.txt', 'r') as file:
            for line in file:
                if '=' in line:
                    key, value = line.strip().split('=')
                    config[key] = value
        
        # Verify required keys
        required_keys = ['OPENAI_API_KEY', 'ASSISTANT_ID']
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            raise ValueError(f"Missing required configuration keys: {', '.join(missing_keys)}")
            
        return config
    except FileNotFoundError:
        raise FileNotFoundError("config.txt file not found. Please create it with OPENAI_API_KEY and ASSISTANT_ID")

def generate_prompt(assistant_id):
    # Create a thread
    thread = client.beta.threads.create()
    
    # Add message to thread
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content='Generate a detailed Midjourney prompt about any topic. Include artistic or photography style, subject matter, lighting, mood, camera angle, and any relevant parameters. Make it creative or cozy and unique. It could be portrait, wide or even panaromic aspect ratio. Do not include "/imagine prompt". For the prompt parameter, please make sure you use "--". Your format response is just pure the prompt: [Your response here]'
    )
    
    # Run the assistant
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
    )
    
    # Wait for completion
    while True:
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
        if run.status == 'completed':
            break
    
    # Get the assistant's response
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    return messages.data[0].content[0].text.value

def save_prompts(prompts, start_from=1):
    # Generate filename with date
    date_str = datetime.now().strftime('%y%m%d')
    filename = f'midjourney_prompts_{date_str}.txt'
    
    # Determine starting prompt number
    start_num = start_from
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            content = file.read()
            existing_prompts = content.count('Prompt ')
            start_num = existing_prompts + 1
    
    # Save prompts to file
    mode = 'a' if os.path.exists(filename) else 'w'
    with open(filename, mode) as file:
        for i, prompt in enumerate(prompts, start_num):
            file.write(f"Prompt {i}:\n{prompt}\n\n")
    
    return filename

def main():
    # Store prompts globally so signal handler can access them
    global generated_prompts
    generated_prompts = []
    
    def signal_handler(signum, frame):
        print("\nGracefully stopping... saving generated prompts...")
        if generated_prompts:
            filename = save_prompts(generated_prompts)
            print(f"\nSaved {len(generated_prompts)} prompts to {filename}")
        sys.exit(0)
    
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate Midjourney prompts using OpenAI Assistant')
    parser.add_argument('-n', '--num-prompts', type=int, default=500,
                      help='Number of prompts to generate (default: 500)')
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    # Set up OpenAI client
    global client
    client = openai.OpenAI(api_key=config['OPENAI_API_KEY'])
    
    # Get assistant ID from config
    assistant_id = config['ASSISTANT_ID']
    
    try:
        for i in range(args.num_prompts):
            try:
                prompt = generate_prompt(assistant_id)
                generated_prompts.append(prompt)
                # Create a progress bar-like output
                progress = (i + 1) / args.num_prompts * 50  # 50 characters wide
                print(f"\rProgress: [{'=' * int(progress)}{' ' * (50 - int(progress))}] {i+1}/{args.num_prompts}", end='')
                print(f"\nGenerated prompt {i+1}/{args.num_prompts}:")
                print(f"{prompt}\n")
            except Exception as e:
                print(f"\nError generating prompt {i+1}: {str(e)}")
                continue
    except KeyboardInterrupt:
        print("\nInterrupted by user. Saving generated prompts...")
        if generated_prompts:
            filename = save_prompts(generated_prompts)
            print(f"\nSaved {len(generated_prompts)} prompts to {filename}")
        sys.exit(0)
    
    # Save all prompts if completed successfully
    if generated_prompts:
        filename = save_prompts(generated_prompts)
        print(f"\nSuccessfully generated {len(generated_prompts)} prompts and saved to {filename}")

if __name__ == "__main__":
    main()
