"""Script simple pour démarrer le serveur."""

import uvicorn

if __name__ == "__main__":
    print("Démarrage du serveur sur http://127.0.0.1:8000")
    print("Documentation: http://127.0.0.1:8000/docs")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

