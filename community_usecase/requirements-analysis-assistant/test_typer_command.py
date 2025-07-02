import typer
import sys

print(f"sys.argv: {sys.argv}")

app = typer.Typer()

@app.command("my-test-command")
def my_test_command():
    print("'my-test-command' executed successfully in new file!")

if __name__ == "__main__":
    app() 