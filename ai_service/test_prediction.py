"""
Test script demonstrating the recommendation model prediction function.
Shows how to get drilling recommendations based on operational parameters.
"""

from api import get_recommendation

# Define test cases with realistic drilling parameters
test_cases = [
    {
        "name": "Conservative Build",
        "inputs": {
            "WOB_klbf": 25,
            "RPM_demo": 80,
            "ROP_ft_hr": 40,
            "PHIF": 0.18,
            "VSH": 0.25,
            "SW": 0.35,
            "KLOGH": 0.45,
            "Torque_kftlb": 2500,
            "Vibration_g": 0.2,
            "DLS_deg_per_100ft": 1.2,
            "Inclination_deg": 30,
            "Azimuth_deg": 90,
            "Formation_Class": "Shale"
        }
    },
    {
        "name": "High ROP Scenario",
        "inputs": {
            "WOB_klbf": 45,
            "RPM_demo": 150,
            "ROP_ft_hr": 120,
            "PHIF": 0.25,
            "VSH": 0.40,
            "SW": 0.50,
            "KLOGH": 0.60,
            "Torque_kftlb": 4500,
            "Vibration_g": 0.45,
            "DLS_deg_per_100ft": 2.5,
            "Inclination_deg": 65,
            "Azimuth_deg": 120,
            "Formation_Class": "Sandstone"
        }
    },
    {
        "name": "Moderate Parameters",
        "inputs": {
            "WOB_klbf": 35,
            "RPM_demo": 110,
            "ROP_ft_hr": 75,
            "PHIF": 0.22,
            "VSH": 0.32,
            "SW": 0.42,
            "KLOGH": 0.52,
            "Torque_kftlb": 3500,
            "Vibration_g": 0.35,
            "DLS_deg_per_100ft": 1.8,
            "Inclination_deg": 50,
            "Azimuth_deg": 105,
            "Formation_Class": "Limestone"
        }
    },
]

def main():
    print("\n" + "="*80)
    print("DRILLING RECOMMENDATION MODEL - TEST PREDICTIONS")
    print("="*80 + "\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test Case {i}: {test_case['name']}")
        print("-" * 80)
        
        # Get prediction
        result = get_recommendation(test_case['inputs'])
        
        # Display results
        print(f"  Recommendation: {result['recommendation']}")
        print(f"  Confidence:     {result['confidence']:.2%}")
        print(f"\n  Class Probabilities:")
        
        for class_name, probability in sorted(result['all_classes'].items(), 
                                             key=lambda x: x[1], 
                                             reverse=True):
            bar_length = int(probability * 50)
            bar = "█" * bar_length + "░" * (50 - bar_length)
            print(f"    {class_name:12} {bar} {probability:.2%}")
        
        print()

if __name__ == "__main__":
    main()
