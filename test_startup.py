"""Script de test pour vérifier le démarrage de l'application."""

import asyncio
import sys

async def test_startup():
    """Tester le démarrage de l'application."""
    try:
        print("Import de l'application...")
        from app.main import app
        print("[OK] Application importee avec succes")
        
        print("\nVerification des dependances...")
        from app.core.dependencies_checker import check_dependencies_on_startup
        await check_dependencies_on_startup()
        print("[OK] Dependances verifiees")
        
        print("\nTest de la connexion a la base de donnees...")
        from app.infrastructure.database.connection import init_db
        await init_db()
        print("[OK] Base de donnees initialisee")
        
        print("\n[OK] Tous les tests sont passes !")
        print("\nVous pouvez maintenant démarrer l'application avec :")
        print("  uvicorn app.main:app --reload")
        
    except Exception as e:
        print(f"\n[ERREUR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_startup())

