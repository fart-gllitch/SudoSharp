#!/usr/bin/env python3

import re
import sys

class SudoSharpInterpreter:
    def __init__(self):
        self.variables = {}
        self.running = True
        self.program_lines = []
        self.current_line = 0
        self.loop_stack = []

    def tokenize(self, line):
        """Split the line into tokens while preserving quoted strings"""
        tokens = []
        i = 0
        while i < len(line):
            # Handle quoted strings
            if line[i] == '"':
                start = i
                i += 1
                while i < len(line) and line[i] != '"':
                    i += 1
                if i < len(line):  # Found closing quote
                    tokens.append(line[start:i+1])
                    i += 1
                else:
                    tokens.append(line[start:])  # Unclosed quote
                    i = len(line)
            # Handle regular tokens
            elif not line[i].isspace():
                start = i
                while i < len(line) and not line[i].isspace():
                    i += 1
                tokens.append(line[start:i])
            else:
                i += 1
        
        return tokens

    def evaluate_expression(self, expr):
        """Evaluate simple expressions"""
        # Handle variable references
        if expr in self.variables:
            return self.variables[expr]
        
        # Handle quoted strings
        if expr.startswith('"') and expr.endswith('"'):
            return expr[1:-1]
        
        # Handle numbers
        try:
            return int(expr)
        except ValueError:
            try:
                return float(expr)
            except ValueError:
                pass
        
        # Handle boolean
        if expr.lower() == "yes" or expr.lower() == "true":
            return True
        if expr.lower() == "no" or expr.lower() == "false":
            return False
            
        return expr  # Return as is if nothing else matched

    def execute_print(self, tokens):
        """Execute print command"""
        if len(tokens) < 2:
            print()  # Print empty line
            return
        
        # If there's a single token in quotes, just print it
        if len(tokens) == 2 and tokens[1].startswith('"') and tokens[1].endswith('"'):
            print(tokens[1][1:-1])
            return
            
        # Otherwise evaluate each token and print them concatenated
        output = ""
        for token in tokens[1:]:
            value = self.evaluate_expression(token)
            output += str(value) + " "
        print(output.rstrip())

    def execute_set(self, tokens):
        """Execute variable assignment"""
        if len(tokens) < 4:
            print("Error: Invalid set command format. Use 'set variable to value'")
            return
        
        var_name = tokens[1]
        
        # Extract and evaluate the value
        value_tokens = tokens[3:]
        
        # Handle simple assignment
        if len(value_tokens) == 1:
            self.variables[var_name] = self.evaluate_expression(value_tokens[0])
            return
        
        # Handle math operations
        if len(value_tokens) == 3:
            left = self.evaluate_expression(value_tokens[0])
            op = value_tokens[1]
            right = self.evaluate_expression(value_tokens[2])
            
            if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
                print(f"Error: Cannot perform math operations on non-numeric values: {left} and {right}")
                return
                
            if op == "plus":
                self.variables[var_name] = left + right
            elif op == "minus":
                self.variables[var_name] = left - right
            elif op == "times":
                self.variables[var_name] = left * right
            elif op == "divided" and value_tokens[2] == "by" and len(value_tokens) >= 4:
                divisor = self.evaluate_expression(value_tokens[3])
                if divisor == 0:
                    print("Error: Division by zero")
                    return
                self.variables[var_name] = left / divisor
            else:
                print(f"Error: Unknown operation '{op}'")
                return

    def execute_ask(self, tokens):
        """Execute input command"""
        if len(tokens) < 3 or tokens[1] != "for":
            print("Error: Invalid ask command format. Use 'ask for variable'")
            return
            
        var_name = tokens[2]
        user_input = input("> ")
        
        # Try to convert to number if possible
        try:
            if '.' in user_input:
                self.variables[var_name] = float(user_input)
            else:
                self.variables[var_name] = int(user_input)
        except ValueError:
            self.variables[var_name] = user_input

    def execute_loop(self, tokens):
        """Execute loop command"""
        if len(tokens) < 4:
            print("Error: Invalid loop command format. Use 'loop through start and end'")
            return
            
        if tokens[1] != "through" or tokens[3] != "and":
            print("Error: Invalid loop command format. Use 'loop through start and end'")
            return
            
        try:
            start = int(self.evaluate_expression(tokens[2]))
            end = int(self.evaluate_expression(tokens[4]))
            
            # Save the current position and the range
            self.loop_stack.append({
                "start": self.current_line,
                "iterator": start,
                "end": end
            })
            
        except ValueError:
            print(f"Error: Loop bounds must be integers, got {tokens[2]} and {tokens[4]}")

    def execute_end_loop(self):
        """Execute end loop command"""
        if not self.loop_stack:
            print("Error: 'end loop' without matching 'loop'")
            return
            
        loop_info = self.loop_stack[-1]
        loop_info["iterator"] += 1
        
        if loop_info["iterator"] <= loop_info["end"]:
            # Continue loop
            self.current_line = loop_info["start"]
        else:
            # End loop
            self.loop_stack.pop()

    def execute_line(self, line):
        """Execute a single line of code"""
        line = line.strip()
        
        # Skip empty lines and comments
        if not line or line.startswith('#'):
            return
        
        tokens = self.tokenize(line)
        if not tokens:
            return
            
        command = tokens[0].lower()
        
        if command == "print":
            self.execute_print(tokens)
        elif command == "set":
            self.execute_set(tokens)
        elif command == "ask":
            self.execute_ask(tokens)
        elif command == "loop":
            self.execute_loop(tokens)
        elif command == "end" and len(tokens) > 1 and tokens[1] == "loop":
            self.execute_end_loop()
        elif command == "exit" or command == "quit":
            self.running = False
        else:
            print(f"Error: Unknown command '{command}'")

    def run_program(self, program):
        """Run a multi-line program"""
        self.program_lines = program.strip().split('\n')
        self.current_line = 0
        
        while self.current_line < len(self.program_lines) and self.running:
            line = self.program_lines[self.current_line]
            self.execute_line(line)
            self.current_line += 1

    def run_interactive(self):
        """Run the interpreter in interactive mode"""
        print("SudoSharp Interpreter v0.1")
        print("Type 'exit' or 'quit' to exit")
        print()
        
        while self.running:
            try:
                line = input("SudoSharp> ")
                
                # Multi-line input
                if line.strip().endswith(':'):
                    print("Enter multiple lines. Type 'end' on a line by itself to finish.")
                    multi_line = [line.strip()[:-1]]  # Remove the colon
                    
                    while True:
                        next_line = input("... ")
                        if next_line.strip() == "end":
                            break
                        multi_line.append(next_line)
                    
                    self.run_program('\n'.join(multi_line))
                else:
                    self.execute_line(line)
                    
            except KeyboardInterrupt:
                print("\nKeyboard interrupt detected")
                self.running = False
            except EOFError:
                print("\nEOF detected")
                self.running = False
            except Exception as e:
                print(f"Error: {e}")

def main():
    interpreter = SudoSharpInterpreter()
    
    if len(sys.argv) > 1:
        # Run the file provided as argument
        try:
            with open(sys.argv[1], 'r') as f:
                program = f.read()
            interpreter.run_program(program)
        except FileNotFoundError:
            print(f"Error: File '{sys.argv[1]}' not found")
        except Exception as e:
            print(f"Error: {e}")
    else:
        # Start interactive mode
        interpreter.run_interactive()

if __name__ == "__main__":
    main()
