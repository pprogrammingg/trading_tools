#!/usr/bin/env python3
"""
Verification script to check scoring logic completeness
"""

import re
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def verify_scoring_components():
    """Verify all scoring components are present"""
    print("=" * 60)
    print("SCORING COMPONENT VERIFICATION")
    print("=" * 60)
    
    file_path = Path(__file__).parent.parent / "technical_analysis.py"
    if not file_path.exists():
        print(f"❌ {file_path} not found")
        return False
    
    content = file_path.read_text()
    
    # Expected scoring components (more flexible patterns)
    expected_components = {
        "RSI": [
            "rsi_multiplier",  # Context-aware
            "rsi_oversold",
            "rsi_overbought",
        ],
        "ADX": [
            "ADXIndicator",
            "adx_very_strong_trend",
            "adx_strong_trend",
        ],
        "CCI": [
            "CCIIndicator",
            "cci_oversold_recovery",
            "cci_overbought",
        ],
        "OBV": [
            "OnBalanceVolumeIndicator",
            "obv_trending_up",
        ],
        "A/D": [
            "AccDistIndexIndicator",
            "acc_dist_trending_up",
        ],
        "MACD": [
            "macd_bullish",
            "MACD",
        ],
        "Moving Averages": [
            "price_above_ema50",
            "price_above_ema200",
            "golden_cross",
        ],
        "GMMA": [
            "gmma_bullish",
            "gmma_early_expansion",
        ],
        "Volume": [
            "volume_above_avg",
            "volume_confirmation",
        ],
        "Momentum": [
            "very_strong_momentum",
            "strong_momentum",
        ],
    }
    
    all_passed = True
    for component, patterns in expected_components.items():
        found = False
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                found = True
                break
        
        if found:
            print(f"✓ {component}: Found")
        else:
            print(f"❌ {component}: Missing")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All scoring components verified")
    else:
        print("❌ Some components missing")
    print("=" * 60)
    
    return all_passed

def verify_imports():
    """Verify all required imports are present"""
    print("\n" + "=" * 60)
    print("IMPORT VERIFICATION")
    print("=" * 60)
    
    file_path = Path(__file__).parent.parent / "technical_analysis.py"
    if not file_path.exists():
        return False
    
    content = file_path.read_text()
    
    required_imports = [
        "ADXIndicator",
        "CCIIndicator",
        "OnBalanceVolumeIndicator",
        "AccDistIndexIndicator",
    ]
    
    all_passed = True
    for imp in required_imports:
        if imp in content:
            print(f"✓ {imp}: Imported")
        else:
            print(f"❌ {imp}: Missing")
            all_passed = False
    
    print("=" * 60)
    return all_passed

if __name__ == "__main__":
    print("\n🔍 Verifying Technical Analysis Scoring Logic\n")
    
    imports_ok = verify_imports()
    components_ok = verify_scoring_components()
    
    if imports_ok and components_ok:
        print("\n✅ All verifications passed!")
        exit(0)
    else:
        print("\n❌ Some verifications failed")
        exit(1)
