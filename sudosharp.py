#!/usr/bin/env python3

import re
import sys
import math

class SudoSharpInterpreter:
    def __init__(self):
        self.variables = {}
        self.running = True
        self.program_lines = []
        self.current_line = 0
        self.loop_stack = []
        
        # Initialize built-in functions and variables
        self.init_builtins()

    def init_builtins(self):
        """Initialize built-in functions and variables"""
        # Basic math functions
        self.variables["abs"] = abs
        self.variables["max"] = max
        self.variables["min"] = min
        self.variables["sum"] = sum
        self.variables["round"] = round
        self.variables["pow"] = pow
        
        # Common math constants
        self.variables["pi"] = math.pi
        self.variables["e"] = math.e
        
        # Type conversion
        self.variables["int"] = int
        self.variables["float"] = float
        self.variables["str"] = str
        
        # Collection functions
        self.variables["len"] = len
        self.variables["sort"] = sorted

    def tokenize(self, line):
        """Split the line into tokens while preserving quoted strings"""
        # Check if this is a comment line
        if line.strip().startswith('$') and not line.strip().lower().startswith('$print'):
            return []  # Skip comment lines
            
        tokens = []
        i = 0
        
        # Special handling for print with interpolation
        if line.strip().lower().startswith('print'):
            tokens.append('print')
            
            # Everything after "print" is considered the print argument
            print_arg = line[line.lower().find('print') + 5:].strip()
            if print_arg:
                tokens.append(print_arg)
            
            return tokens
        
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

    def process_string_interpolation(self, text):
        """Process string interpolation with $variable$ syntax"""
        # Find all patterns of $variable$
        pattern = r'\$([a-zA-Z0-9_]+)\$'
        
        def replace_var(match):
            var_name = match.group(1)
            if var_name in self.variables:
                return str(self.variables[var_name])
            return f"${var_name}$"  # Keep as is if variable not found
            
        # Replace all occurrences
        return re.sub(pattern, replace_var, text)

    def evaluate_expression(self, expr):
        """Evaluate simple expressions"""
        # Process string interpolation first
        if isinstance(expr, str) and '$' in expr:
            expr = self.process_string_interpolation(expr)
        
        # Handle variable references
        if expr in self.variables:
            return self.variables[expr]
        
        # Handle quoted strings
        if isinstance(expr, str) and expr.startswith('"') and expr.endswith('"'):
            return expr[1:-1]
        
        # Handle numbers
        try:
            if isinstance(expr, str):
                if '.' in expr:
                    return float(expr)
                else:
                    return int(expr)
            return expr  # Already a number
        except ValueError:
            pass
        
        # Handle boolean
        if isinstance(expr, str):
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
        
        # Process string interpolation in the print argument
        if '$' in tokens[1]:
            processed_text = self.process_string_interpolation(tokens[1])
            print(processed_text)
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
        if tokens[2].lower() != "to":
            print("Error: Invalid set command format. Use 'set variable to value'")
            return
            
        value_tokens = tokens[3:]
        
        # Handle simple assignment
        if len(value_tokens) == 1:
            self.variables[var_name] = self.evaluate_expression(value_tokens[0])
            return
        
        # Handle math operations
        if len(value_tokens) >= 3:
            left = self.evaluate_expression(value_tokens[0])
            op = value_tokens[1].lower()
            
            # Handle division which has a different syntax
            if op == "divided" and len(value_tokens) >= 3 and value_tokens[2].lower() == "by":
                if len(value_tokens) < 4:
                    print("Error: Invalid division format. Use 'divided by value'")
                    return
                right = self.evaluate_expression(value_tokens[3])
                if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
                    print(f"Error: Cannot perform division on non-numeric values: {left} and {right}")
                    return
                if right == 0:
                    print("Error: Division by zero")
                    return
                self.variables[var_name] = left / right
                return
                
            # Handle other operations
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
            else:
                print(f"Error: Unknown operation '{op}'")
                return

    def execute_ask(self, tokens):
        """Execute input command"""
        if len(tokens) < 3 or tokens[1].lower() != "for":
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
        if len(tokens) < 5:
            print("Error: Invalid loop command format. Use 'loop through start and end'")
            return
            
        if tokens[1].lower() != "through" or tokens[3].lower() != "and":
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
            
            # Set the loop variable 'i'
            self.variables["i"] = start
            
        except ValueError:
            print(f"Error: Loop bounds must be integers, got {tokens[2]} and {tokens[4]}")

    def execute_end_loop(self):
        """Execute end loop command"""
        if not self.loop_stack:
            print("Error: 'end loop' without matching 'loop'")
            return
            
        loop_info = self.loop_stack[-1]
        loop_info["iterator"] += 1
        
        # Update the loop variable 'i'
        self.variables["i"] = loop_info["iterator"]
        
        if loop_info["iterator"] <= loop_info["end"]:
            # Continue loop
            self.current_line = loop_info["start"]
        else:
            # End loop
            self.loop_stack.pop()

    def execute_import(self, tokens):
        """Import built-in modules or custom code"""
        if len(tokens) < 2:
            print("Error: Invalid import command. Use 'import module'")
            return
            
        module_name = tokens[1].lower()
        
        if module_name == "math":
            # Import common math functions
            self.variables["sin"] = math.sin
            self.variables["cos"] = math.cos
            self.variables["tan"] = math.tan
            self.variables["sqrt"] = math.sqrt
            self.variables["log"] = math.log
            self.variables["floor"] = math.floor
            self.variables["ceil"] = math.ceil
            print(f"Imported math module")
        else:
            print(f"Error: Module '{module_name}' not found")

    def execute_if(self, tokens):
        """Execute if statement (simplified)"""
        # Placeholder for future implementation
        print("If statements are not yet implemented")

    def execute_line(self, line):
        """Execute a single line of code"""
        line = line.strip()
        
        # Skip empty lines
        if not line:
            return
            
        # Skip comments that start with # or $
        if line.startswith('#') or (line.startswith('$') and not line.lower().startswith('$print')):
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
        elif command == "end" and len(tokens) > 1 and tokens[1].lower() == "loop":
            self.execute_end_loop()
        elif command == "import":
            self.execute_import(tokens)
        elif command == "if":
            self.execute_if(tokens)
        elif command == "exit" or command == "quit":
            self.running = False
        elif command == "help":
            self.show_help()
        else:
            print(f"Error: Unknown command '{command}'")

    def show_help(self):
        """Show help information"""
        print("\nSudoSharp Language Help")
        print("======================")
        print("Commands:")
        print("  print [text/$variable$/etc] - Output text to console. Use $var$ for variable interpolation.")
        print("  set variable to value - Assign a value to a variable")
        print("  ask for variable - Get user input and store it in a variable")
        print("  loop through start and end - Loop from start to end values")
        print("  end loop - End a loop block")
        print("  import module - Import a module (currently only 'math' is supported)")
        print("  exit/quit - Exit the program")
        print("  help - Show this help message")
        print("\nMath Operations:")
        print("  set result to value1 plus value2")
        print("  set result to value1 minus value2")
        print("  set result to value1 times value2")
        print("  set result to value1 divided by value2")
        print("\nBuilt-in Functions:")
        print("  abs, max, min, sum, round, pow, int, float, str, len, sort")
        print("\nComments:")
        print("  $ This is a comment")
        print("  # This is also a comment")

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
        print("SudoSharp Interpreter v0.2")
        print("Type 'help' for available commands")
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
