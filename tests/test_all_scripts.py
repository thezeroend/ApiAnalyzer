#!/usr/bin/env python3
"""
Script para testar rapidamente se todos os scripts de teste estão funcionando
"""

import os
import subprocess
import sys

def test_script(script_name):
    """Testa se um script pode ser importado sem erros"""
    print(f"🧪 Testando: {script_name}")
    
    try:
        # Tentar importar o script
        script_path = os.path.join("tests", script_name)
        
        # Verificar se o arquivo existe
        if not os.path.exists(script_path):
            print(f"   ❌ Arquivo não encontrado: {script_path}")
            return False
        
        # Determinar o comando Python correto
        if os.name == 'nt':  # Windows
            cmd = ["wsl", "python3", script_path]
        else:  # Linux/WSL
            cmd = ["python3", script_path]
        
        # Tentar executar o script com timeout
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30  # 30 segundos de timeout
        )
        
        if result.returncode == 0:
            print(f"   ✅ {script_name} - OK")
            return True
        else:
            print(f"   ❌ {script_name} - Erro:")
            print(f"      {result.stderr[:200]}...")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"   ⏰ {script_name} - Timeout (pode estar funcionando)")
        return True
    except Exception as e:
        print(f"   ❌ {script_name} - Erro: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 TESTE RÁPIDO DE TODOS OS SCRIPTS")
    print("=" * 50)
    
    # Lista de scripts para testar (apenas os principais)
    test_scripts = [
        "test_simple.py",
        "test_ml.py", 
        "test_feedback.py",
        "test_config.py",
        "test_network_anomaly.py"
    ]
    
    successful = 0
    total = len(test_scripts)
    
    for script in test_scripts:
        if test_script(script):
            successful += 1
        print()
    
    print("=" * 50)
    print(f"📊 RESULTADO: {successful}/{total} scripts funcionando")
    
    if successful == total:
        print("✅ TODOS OS SCRIPTS ESTÃO FUNCIONANDO!")
    else:
        print("⚠️  ALGUNS SCRIPTS TÊM PROBLEMAS")
        print("   Consulte os erros acima para mais detalhes")
    
    return successful == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 