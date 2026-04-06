"""
Quick-start example: How to use the drilling recommendation model
"""

from api import get_recommendation

def main():
    # Example 1: Simple prediction
    print("=" * 70)
    print("DRILLING RECOMMENDATION MODEL - QUICK START")
    print("=" * 70)
    
    # Define drilling parameters
    drilling_inputs = {
        "WOB_klbf": 40,              # Weight on bit
        "RPM_demo": 120,             # Rotations per minute
        "ROP_ft_hr": 85,             # Rate of penetration
        "PHIF": 0.20,                # Porosity
        "VSH": 0.30,                 # Shale volume
        "SW": 0.40,                  # Water saturation
        "KLOGH": 0.50,               # Permeability log
        "Torque_kftlb": 3800,        # Torque
        "Vibration_g": 0.40,         # Vibration
        "DLS_deg_per_100ft": 2.0,    # Dogleg severity
        "Inclination_deg": 55,       # Inclination
        "Azimuth_deg": 100,          # Azimuth
        "Formation_Class": "Shale"   # Formation type
    }
    
    # Get prediction
    result = get_recommendation(drilling_inputs)
    
    # Display results
    print("\nInput Parameters:")
    print(f"  WOB: {drilling_inputs['WOB_klbf']} klbf")
    print(f"  RPM: {drilling_inputs['RPM_demo']}")
    print(f"  ROP: {drilling_inputs['ROP_ft_hr']} ft/hr")
    print(f"  Formation: {drilling_inputs['Formation_Class']}")
    
    print("\nModel Prediction:")
    print(f"  ✓ Recommendation: {result['recommendation']}")
    print(f"  ✓ Confidence: {result['confidence']:.1%}")
    
    print("\nProbabilities for all classes:")
    for class_name, prob in sorted(result['all_classes'].items(), 
                                  key=lambda x: x[1], reverse=True):
        print(f"  - {class_name:12}: {prob:.1%}")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
