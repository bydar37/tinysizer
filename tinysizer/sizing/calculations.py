import numpy as np

class Calculator:
    def __init__(self, parent=None):
        self.parent = parent
        self.failures = None
        self.materials = None
        
        # Material database with ultimate strengths (example values in MPa)
        self.material_properties = {
            "Aluminum 6061-T6": {"ultimate_strength": 310, "yield_strength": 276, "density": 2700},
            "Steel AISI 4130": {"ultimate_strength": 670, "yield_strength": 435, "density": 7850},
            "Titanium Ti-6Al-4V": {"ultimate_strength": 950, "yield_strength": 880, "density": 4430},
            "Composite Carbon/Epoxy": {"ultimate_strength": 1500, "yield_strength": 1200, "density": 1600},
            "Aluminum 7075-T6": {"ultimate_strength": 572, "yield_strength": 503, "density": 2810},
            "Steel 4340": {"ultimate_strength": 745, "yield_strength": 470, "density": 7850}
        }
    
    def get_material_allowable(self, material_name, failure_mode="ultimate"):
        """Get material allowable stress based on failure mode"""
        if material_name not in self.material_properties:
            raise ValueError(f"Material {material_name} not found in database")
        
        props = self.material_properties[material_name]
        if failure_mode == "ultimate":
            return props["ultimate_strength"]
        elif failure_mode == "yield":
            return props["yield_strength"]
        else:
            return props["ultimate_strength"]
    
    def extract_stress_data(self, model_data, property_id):
        """Extract stress data for a specific property ID from FEA results"""
        try:
            # This is a placeholder - you'll need to adapt based on your FEA data structure
            # Assuming model_data has stress results stored somewhere
            
            if not hasattr(model_data, 'stress_results'):
                # If no stress results, return dummy data for demonstration
                print("Warning: No stress results found, using dummy data")
                return {
                    'von_mises': np.random.uniform(50, 200, 100),  # Dummy von mises stresses
                    'principal_stress_1': np.random.uniform(40, 180, 100),
                    'principal_stress_2': np.random.uniform(-50, 100, 100),
                    'element_ids': list(range(1, 101))
                }
            
            # Extract elements with the specified property ID
            elements_with_property = []
            stress_data = {'von_mises': [], 'principal_stress_1': [], 'principal_stress_2': [], 'element_ids': []}
            
            # Find elements using this property
            for elem_id, element in model_data.bdf.elements.items():
                if hasattr(element, 'pid') and element.pid == property_id:
                    elements_with_property.append(elem_id)
            
            # Extract stress data for these elements
            for elem_id in elements_with_property:
                if elem_id in model_data.stress_results:
                    stress = model_data.stress_results[elem_id]
                    stress_data['von_mises'].append(stress.get('von_mises', 0))
                    stress_data['principal_stress_1'].append(stress.get('principal_1', 0))
                    stress_data['principal_stress_2'].append(stress.get('principal_2', 0))
                    stress_data['element_ids'].append(elem_id)
            
            return stress_data
            
        except Exception as e:
            print(f"Error extracting stress data: {e}")
            # Return dummy data as fallback
            return {
                'von_mises': np.random.uniform(50, 200, 50),
                'principal_stress_1': np.random.uniform(40, 180, 50),
                'principal_stress_2': np.random.uniform(-50, 100, 50),
                'element_ids': list(range(1, 51))
            }
    
    def calculate_von_mises_rf(self, stress_data, allowable_stress):
        """Calculate Reserve Factor for Von Mises failure"""
        von_mises_stresses = np.array(stress_data['von_mises'])
        
        # Calculate RF for each element: RF = Allowable / Applied
        rfs = allowable_stress / von_mises_stresses
        
        return {
            'element_rfs': rfs,
            'min_rf': np.min(rfs),
            'max_rf': np.max(rfs),
            'avg_rf': np.mean(rfs),
            'critical_element': stress_data['element_ids'][np.argmin(rfs)],
            'max_stress': np.max(von_mises_stresses)
        }
    
    def calculate_principal_stress_rf(self, stress_data, allowable_stress):
        """Calculate Reserve Factor for Maximum Principal Stress failure"""
        principal_1 = np.array(stress_data['principal_stress_1'])
        principal_2 = np.array(stress_data['principal_stress_2'])
        
        # Maximum principal stress is the larger of the two
        max_principal = np.maximum(np.abs(principal_1), np.abs(principal_2))
        
        # Calculate RF for each element
        rfs = allowable_stress / max_principal
        
        return {
            'element_rfs': rfs,
            'min_rf': np.min(rfs),
            'max_rf': np.max(rfs),
            'avg_rf': np.mean(rfs),
            'critical_element': stress_data['element_ids'][np.argmin(rfs)],
            'max_stress': np.max(max_principal)
        }
    
    def size_for_target_rf(self, model_data, property_id, material, failure_type, 
                          thickness_range, target_rf=1.1, assembly_type="web"):
        """
        Size the structure to achieve target Reserve Factor
        
        Args:
            model_data: FEA model data
            property_id: Property ID to size
            material: Material name
            failure_type: Failure criterion (e.g., "Von Mises")
            thickness_range: (min, max, step) for thickness
            target_rf: Target reserve factor (default 1.1 for 10% margin)
            assembly_type: "web" or "cap"
        """
        
        min_t, max_t, step_t = thickness_range
        allowable_stress = self.get_material_allowable(material)
        
        print(f"Sizing {assembly_type} assembly with {material}")
        print(f"Allowable stress: {allowable_stress} MPa")
        print(f"Target RF: {target_rf}")
        print(f"Thickness range: {min_t} to {max_t} mm, step: {step_t} mm")
        
        # Extract stress data (this would be from original thickness)
        stress_data = self.extract_stress_data(model_data, property_id)
        
        # Sizing iteration
        results = []
        thickness_values = np.arange(min_t, max_t + step_t, step_t)
        
        prop = model_data.bdf.properties[property_id]
        base_thickness = (
            prop.t if prop.type == "PSHELL" else 
            prop.thicknesses[0] if prop.type == "PCOMP" else 1.0
        )

        for thickness in thickness_values:
            # Scale stresses inversely with thickness (simplified assumption)
            # In reality, you'd need to re-run FEA or use scaling relationships
            stress_scale_factor = base_thickness / thickness
            
            # Scale the stress data
            scaled_stress_data = {
                'von_mises': [s * stress_scale_factor for s in stress_data['von_mises']],
                'principal_stress_1': [s * stress_scale_factor for s in stress_data['principal_stress_1']],
                'principal_stress_2': [s * stress_scale_factor for s in stress_data['principal_stress_2']],
                'element_ids': stress_data['element_ids']
            }
            
            # Calculate RF based on failure type
            if failure_type == "Von Mises":
                rf_results = self.calculate_von_mises_rf(scaled_stress_data, allowable_stress)
            elif failure_type == "Maximum Principal Stress":
                rf_results = self.calculate_principal_stress_rf(scaled_stress_data, allowable_stress)
            else:
                # Default to Von Mises
                rf_results = self.calculate_von_mises_rf(scaled_stress_data, allowable_stress)
            
            results.append({
                'thickness': thickness,
                'min_rf': rf_results['min_rf'],
                'avg_rf': rf_results['avg_rf'],
                'max_rf': rf_results['max_rf'],
                'critical_element': rf_results['critical_element'],
                'max_stress': rf_results['max_stress']
            })
            
            # Check if we've reached target RF
            if rf_results['min_rf'] >= target_rf:
                print(f"Target RF achieved at thickness: {thickness} mm")
                print(f"Minimum RF: {rf_results['min_rf']:.3f}")
                print(f"Critical element: {rf_results['critical_element']}")
                break
        
        return results
    
    def rf_materialStrength(self, materials, failure_types, model_data=None, property_id=None, 
                           thickness_range=None, assembly_type="web"):
        """
        Main sizing function called from UI
        """
        if not materials or not failure_types:
            print("No materials or failure types selected")
            return None
        
        if not model_data or property_id is None:
            print("No model data or property ID provided")
            return None
        
        # Use first material and failure type for now (could be extended for multiple)
        material = materials[0]
        failure_type = failure_types[0]
        
        print(f"Starting analysis for Material: {material}, Failure: {failure_type}")
        
        # Perform sizing
        results = self.size_for_target_rf(
            model_data=model_data,
            property_id=property_id,
            material=material,
            failure_type=failure_type,
            thickness_range=thickness_range,
            assembly_type=assembly_type
        )
        
        return results