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
    
    def get_available_subcases(self):
        """Get all available subcase IDs from OP2 results"""
        try:
            op2_data = self.parent.model_data.op2
            
            # Check different result types for available subcases
            available_subcases = set()
            
            if hasattr(op2_data, 'displacements'):
                available_subcases.update(op2_data.displacements.keys())
            
            if hasattr(op2_data, 'cquad4_stress'):
                available_subcases.update(op2_data.cquad4_stress.keys())
                
            if hasattr(op2_data, 'cquad4_force'):
                available_subcases.update(op2_data.cquad4_force.keys())
            
            return sorted(list(available_subcases))
            
        except Exception as e:
            print(f"Error getting available subcases: {e}")
            return [1]  # Default fallback
    
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
    
    def extract_stress_data(self, property_id, subcase_id=1, scale_factor=1.0):
        """
        Extract stress data from pyNastran OP2 results for elements with specific property ID
        
        Args:
            property_id: Property ID to filter elements
            subcase_id: Subcase ID (default 1)
            scale_factor: Factor to scale stresses (for parametric studies)
        
        Returns:
            dict: Stress data with von_mises, principal stresses, and element IDs
        """

        try:
            # Get OP2 stress results
            op2_data = self.parent.model_data.op2
            
            #düzenlendi -ymn
            if not hasattr(op2_data, 'cquad4_stress'):
                #raise ValueError(f"No CQUAD4 stress results found for subcase {subcase_id}")
                stress_df = op2_data.cquad4_stress[subcase_id].dataframe.reset_index()
                print(f"Found shell stresses for subcase {subcase_id}")
            else:
                """
                columns for composite stress:
                Index(['o11', 'o22', 't12', 't1z', 't2z', 'angle', 'major', 'minor',      
                'max_shear'],
                """
                stress_df = op2_data.cquad4_composite_stress[subcase_id].dataframe.reset_index()
                print(f"Found shell stresses for subcase {subcase_id}")

            # Get BDF model for property filtering
            bdf_model = self.parent.model_data.bdf
            
            # Find elements with the specified property ID
            target_elements = []
            for elem_id, element in bdf_model.elements.items():
                if hasattr(element, 'pid') and element.pid == property_id:
                    target_elements.append(elem_id)
            
            if not target_elements:
                raise ValueError(f"No elements found with property ID {property_id}")
            
            # Extract stress data for target elements
            stress_data = {
                'von_mises': [],
                'principal_stress_1': [],
                'principal_stress_2': [],
                'element_ids': [],
                'max_shear': []
            }
            
            # Get stress data from OP2
            element_ids = list(stress_df["ElementID"])
            von_mises = stress_df['o11'] #daha sonra mises hesaplariz şimdilik p1 gibi
            max_principal = abs(stress_df['o11'])
            min_principal = abs(stress_df['o22'])
            max_shear = abs(stress_df['t12'])
            
            # Filter for target elements and apply scaling
            for i, elem_id in enumerate(element_ids):
                if elem_id in target_elements:
                    stress_data['element_ids'].append(elem_id)
                    stress_data['von_mises'].append(von_mises[i] * scale_factor)
                    stress_data['principal_stress_1'].append(max_principal[i] * scale_factor)
                    stress_data['principal_stress_2'].append(min_principal[i] * scale_factor)
                    stress_data['max_shear'].append(max_shear[i] * scale_factor)
            
            if not stress_data['element_ids']:
                raise ValueError(f"No stress data found for elements with property ID {property_id}")
            
            # Convert to numpy arrays for easier processing
            for key in ['von_mises', 'principal_stress_1', 'principal_stress_2', 'max_shear']:
                stress_data[key] = np.array(stress_data[key])
            
            return stress_data
            
        except Exception as e:
            print(f"Error extracting stress data for subcase {subcase_id}: {e}")
            return None
    
    def extract_displacement_data(self, property_id, subcase_id=1, scale_factor=1.0):
        """
        Extract displacement data from pyNastran OP2 results
        
        Args:
            property_id: Property ID to filter elements
            subcase_id: Subcase ID (default 1)
            scale_factor: Factor to scale displacements
        
        Returns:
            dict: Displacement data with translations and rotations
        """
        try:
            op2_data = self.parent.model_data.op2
            
            if not hasattr(op2_data, 'displacements') or subcase_id not in op2_data.displacements:
                raise ValueError(f"No displacement results found for subcase {subcase_id}")
            
            disp_obj = op2_data.displacements[subcase_id]
            
            # Get nodes connected to elements with target property ID
            bdf_model = self.parent.model_data.bdf
            target_nodes = set()
            
            for elem_id, element in bdf_model.elements.items():
                if hasattr(element, 'pid') and element.pid == property_id:
                    target_nodes.update(element.nodes)
            
            # Extract displacement data
            disp_data = {
                'node_ids': [],
                'translation_x': [],
                'translation_y': [],
                'translation_z': [],
                'rotation_x': [],
                'rotation_y': [],
                'rotation_z': [],
                'magnitude': []
            }
            
            node_ids = disp_obj.node_gridtype[:, 0]
            translations = disp_obj.data[0, :, :3]  # [T1, T2, T3]
            rotations = disp_obj.data[0, :, 3:6]    # [R1, R2, R3]
            
            for i, node_id in enumerate(node_ids):
                if node_id in target_nodes:
                    disp_data['node_ids'].append(int(node_id))
                    disp_data['translation_x'].append(translations[i, 0] * scale_factor)
                    disp_data['translation_y'].append(translations[i, 1] * scale_factor)
                    disp_data['translation_z'].append(translations[i, 2] * scale_factor)
                    disp_data['rotation_x'].append(rotations[i, 0] * scale_factor)
                    disp_data['rotation_y'].append(rotations[i, 1] * scale_factor)
                    disp_data['rotation_z'].append(rotations[i, 2] * scale_factor)
                    
                    # Calculate magnitude
                    mag = np.sqrt(translations[i, 0]**2 + translations[i, 1]**2 + translations[i, 2]**2)
                    disp_data['magnitude'].append(mag * scale_factor)
            
            return disp_data
            
        except Exception as e:
            print(f"Error extracting displacement data for subcase {subcase_id}: {e}")
            return None
    
    def extract_force_data(self, property_id, subcase_id=1, scale_factor=1.0):
        """
        Extract force data from pyNastran OP2 results
        
        Args:
            property_id: Property ID to filter elements
            subcase_id: Subcase ID (default 1)
            scale_factor: Factor to scale forces
        
        Returns:
            dict: Force data for elements
        """
        try:
            op2_data = self.parent.model_data.op2
            
            # Check for different force result types
            force_results = None
            if hasattr(op2_data, 'cquad4_force') and subcase_id in op2_data.cquad4_force:
                force_results = op2_data.cquad4_force[subcase_id]
            elif hasattr(op2_data, 'grid_point_forces') and subcase_id in op2_data.grid_point_forces:
                force_results = op2_data.grid_point_forces[subcase_id]
            else:
                raise ValueError(f"No force results found for subcase {subcase_id}")
            
            # Filter and extract force data similar to stress extraction
            bdf_model = self.parent.model_data.bdf
            target_elements = [elem_id for elem_id, element in bdf_model.elements.items() 
                             if hasattr(element, 'pid') and element.pid == property_id]
            
            force_data = {
                'element_ids': [],
                'forces': [],
                'moments': []
            }
            
            # Extract based on result type
            if hasattr(force_results, 'element'):
                element_ids = force_results.element
                for i, elem_id in enumerate(element_ids):
                    if elem_id in target_elements:
                        force_data['element_ids'].append(elem_id)
                        # Scale forces
                        force_data['forces'].append(force_results.data[0, i, :] * scale_factor)
            
            return force_data
            
        except Exception as e:
            print(f"Error extracting force data for subcase {subcase_id}: {e}")
            return None
    
    def calculate_von_mises_rf(self, stress_data, allowable_stress):
        """Calculate Reserve Factor for Von Mises failure"""
        von_mises_stresses = stress_data['von_mises']
        
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
        principal_1 = stress_data['principal_stress_1']
        principal_2 = stress_data['principal_stress_2']
        
        # Maximum principal stress is the larger of the two absolute values
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
    
    def find_critical_subcase(self, property_id, material, failure_type, thickness):
        """
        Find the critical subcase (minimum RF) across all available subcases
        
        Args:
            property_id: Property ID to analyze
            material: Material name
            failure_type: Failure criterion
            thickness: Thickness for scaling
            
        Returns:
            dict: Critical subcase information
        """
        available_subcases = self.get_available_subcases()
        allowable_stress = self.get_material_allowable(material)
        
        # Get base thickness for scaling
        prop = self.parent.model_data.bdf.properties[property_id]
        base_thickness = (
            prop.t if prop.type == "PSHELL" else 
            prop.thicknesses[0] if prop.type == "PCOMP" else 1.0
        )
        stress_scale_factor = base_thickness / thickness
        
        critical_results = {
            'critical_subcase_id': None,
            'min_rf_overall': float('inf'),
            'subcase_results': {}
        }
        
        print(f"Analyzing {len(available_subcases)} subcases: {available_subcases}")
        
        for subcase_id in available_subcases:
            try:
                # Extract stress data for this subcase
                stress_data = self.extract_stress_data(property_id, subcase_id, stress_scale_factor)
                
                if stress_data is None:
                    continue
                
                # Calculate RF based on failure type
                if failure_type == "Von Mises":
                    rf_results = self.calculate_von_mises_rf(stress_data, allowable_stress)
                elif failure_type == "Maximum Principal Stress":
                    rf_results = self.calculate_principal_stress_rf(stress_data, allowable_stress)
                else:
                    rf_results = self.calculate_von_mises_rf(stress_data, allowable_stress)
                
                # Store results for this subcase
                critical_results['subcase_results'][subcase_id] = {
                    'min_rf': rf_results['min_rf'],
                    'avg_rf': rf_results['avg_rf'],
                    'max_rf': rf_results['max_rf'],
                    'critical_element': rf_results['critical_element'],
                    'max_stress': rf_results['max_stress']
                }
                
                # Check if this is the new critical subcase
                if rf_results['min_rf'] < critical_results['min_rf_overall']:
                    critical_results['min_rf_overall'] = rf_results['min_rf']
                    critical_results['critical_subcase_id'] = subcase_id
                
                print(f"Subcase {subcase_id}: Min RF = {rf_results['min_rf']:.3f}")
                
            except Exception as e:
                print(f"Error analyzing subcase {subcase_id}: {e}")
                continue
        
        return critical_results
    
    def find_critical_combination(self, property_id, materials, failure_types, thickness):
        """
        Find the critical combination of material, failure type, and subcase for a given thickness
        
        Args:
            property_id: Property ID to analyze
            materials: List of material names
            failure_types: List of failure criteria
            thickness: Thickness for analysis
            
        Returns:
            dict: Critical combination information
        """
        available_subcases = self.get_available_subcases()
        
        # Get base thickness for scaling
        prop = self.parent.model_data.bdf.properties[property_id]
        base_thickness = (
            prop.t if prop.type == "PSHELL" else 
            prop.thicknesses[0] if prop.type == "PCOMP" else 1.0
        )
        stress_scale_factor = base_thickness / thickness
        
        critical_results = {
            'critical_material': None,
            'critical_failure_type': None,
            'critical_subcase_id': None,
            'min_rf_overall': float('inf'),
            'critical_element': None,
            'max_stress': None,
            'all_combinations': {}
        }
        
        # Iterate through all combinations
        for material in materials:
            allowable_stress = self.get_material_allowable(material)
            
            for failure_type in failure_types:
                combination_key = f"{material}_{failure_type}"
                critical_results['all_combinations'][combination_key] = {
                    'subcase_results': {},
                    'min_rf_for_combination': float('inf'),
                    'critical_subcase': None
                }
                
                for subcase_id in available_subcases:
                    try:
                        # Extract stress data for this subcase
                        stress_data = self.extract_stress_data(property_id, subcase_id, stress_scale_factor)
                        
                        if stress_data is None:
                            continue
                        
                        # Calculate RF based on failure type
                        if failure_type == "Von Mises":
                            rf_results = self.calculate_von_mises_rf(stress_data, allowable_stress)
                        elif failure_type == "Maximum Principal Stress":
                            rf_results = self.calculate_principal_stress_rf(stress_data, allowable_stress)
                        else:
                            rf_results = self.calculate_von_mises_rf(stress_data, allowable_stress)
                        
                        # Store results for this combination and subcase
                        critical_results['all_combinations'][combination_key]['subcase_results'][subcase_id] = {
                            'min_rf': rf_results['min_rf'],
                            'avg_rf': rf_results['avg_rf'],
                            'max_rf': rf_results['max_rf'],
                            'critical_element': rf_results['critical_element'],
                            'max_stress': rf_results['max_stress'],
                            'allowable_stress': allowable_stress
                        }
                        
                        # Check if this is critical for this combination
                        if rf_results['min_rf'] < critical_results['all_combinations'][combination_key]['min_rf_for_combination']:
                            critical_results['all_combinations'][combination_key]['min_rf_for_combination'] = rf_results['min_rf']
                            critical_results['all_combinations'][combination_key]['critical_subcase'] = subcase_id
                        
                        # Check if this is the overall critical condition
                        if rf_results['min_rf'] < critical_results['min_rf_overall']:
                            critical_results['min_rf_overall'] = rf_results['min_rf']
                            critical_results['critical_material'] = material
                            critical_results['critical_failure_type'] = failure_type
                            critical_results['critical_subcase_id'] = subcase_id
                            critical_results['critical_element'] = rf_results['critical_element']
                            critical_results['max_stress'] = rf_results['max_stress']
                        
                    except Exception as e:
                        print(f"Error analyzing {material}/{failure_type}/subcase {subcase_id}: {e}")
                        continue
        
        return critical_results

    def size_for_target_rf_multi(self, property_id, materials, failure_types, 
                                thickness_range, target_rf=1.1, assembly_type="web"):
        """
        Size the structure considering all materials, failure types, and subcases
        
        Args:
            property_id: Property ID to size
            materials: List of material names
            failure_types: List of failure criteria
            thickness_range: (min, max, step) for thickness
            target_rf: Target reserve factor (default 1.1 for 10% margin)
            assembly_type: "web" or "cap"
        """
        
        min_t, max_t, step_t = thickness_range
        available_subcases = self.get_available_subcases()
        
        print(f"Multi-condition sizing for {assembly_type} assembly")
        print(f"Materials: {materials}")
        print(f"Failure types: {failure_types}")
        print(f"Available subcases: {available_subcases}")
        print(f"Target RF: {target_rf}")
        print(f"Thickness range: {min_t} to {max_t} mm, step: {step_t} mm")
        print(f"Total combinations to analyze: {len(materials)} × {len(failure_types)} × {len(available_subcases)}")
        
        # Sizing iteration
        results = []
        thickness_values = np.arange(min_t, max_t + step_t, step_t)
        
        for thickness in thickness_values:
            print(f"\n{'='*50}")
            print(f"Analyzing thickness: {thickness} mm")
            print(f"{'='*50}")
            
            # Find critical combination for this thickness
            critical_info = self.find_critical_combination(property_id, materials, failure_types, thickness)
            
            if critical_info['critical_material'] is None:
                print(f"No valid results for thickness {thickness}")
                continue
            
            # Get the critical condition details
            critical_material = critical_info['critical_material']
            critical_failure = critical_info['critical_failure_type']
            critical_subcase = critical_info['critical_subcase_id']
            min_rf_overall = critical_info['min_rf_overall']
            
            # Get detailed results for the critical combination
            critical_combo_key = f"{critical_material}_{critical_failure}"
            critical_combo_data = critical_info['all_combinations'][critical_combo_key]['subcase_results'][critical_subcase]
            
            results.append({
                'thickness': thickness,
                'min_rf': min_rf_overall,
                'avg_rf': critical_combo_data['avg_rf'],
                'max_rf': critical_combo_data['max_rf'],
                'critical_element': critical_info['critical_element'],
                'max_stress': critical_info['max_stress'],
                'critical_material': critical_material,
                'critical_failure_type': critical_failure,
                'critical_subcase_id': critical_subcase,
                'critical_allowable_stress': critical_combo_data['allowable_stress'],
                'all_combinations': critical_info['all_combinations']
            })
            
            print(f"CRITICAL CONDITION:")
            print(f"  Material: {critical_material}")
            print(f"  Failure Type: {critical_failure}")
            print(f"  Subcase: {critical_subcase}")
            print(f"  Min RF: {min_rf_overall:.3f}")
            print(f"  Critical Element: {critical_info['critical_element']}")
            print(f"  Max Stress: {critical_info['max_stress']:.1f} MPa")
            print(f"  Allowable: {critical_combo_data['allowable_stress']} MPa")
            
            # Show summary of all combinations
            print(f"\nSUMMARY OF ALL COMBINATIONS:")
            for combo_key, combo_data in critical_info['all_combinations'].items():
                material_name, failure_name = combo_key.split('_', 1)
                min_rf_combo = combo_data['min_rf_for_combination']
                critical_sc = combo_data['critical_subcase']
                print(f"  {material_name} / {failure_name}: Min RF = {min_rf_combo:.3f} (Subcase {critical_sc})")
            
            # Check if we've reached target RF
            if min_rf_overall >= target_rf:
                print(f"\n{'='*50}")
                print(f"TARGET RF ACHIEVED!")
                print(f"Optimum thickness: {thickness} mm")
                print(f"Minimum RF: {min_rf_overall:.3f}")
                print(f"Critical condition: {critical_material} / {critical_failure} / Subcase {critical_subcase}")
                print(f"{'='*50}")
                break
        
        return results
    
    def rf_materialStrength(self, materials, failure_types, property_id=None, 
                           thickness_range=None, assembly_type="web", target_rf=1.1):
        """
        Main sizing function called from UI
        Analyzes all materials, failure types, and subcases to find optimum sizing
        
        Args:
            materials: List of material names
            failure_types: List of failure criteria
            property_id: Property ID to analyze
            thickness_range: (min, max, step) for thickness
            assembly_type: "web" or "cap"
            target_rf: Target reserve factor (default 1.1)
        """
        if not materials or not failure_types:
            print("No materials or failure types selected")
            return None
        
        if not self.parent or not hasattr(self.parent, 'model_data') or property_id is None:
            print("No model data or property ID provided")
            return None
        
        print(f"Starting comprehensive analysis:")
        print(f"Materials: {materials}")
        print(f"Failure types: {failure_types}")
        print(f"Assembly type: {assembly_type}")
        print(f"Target RF: {target_rf}")
        
        available_subcases = self.get_available_subcases()
        print(f"Available subcases: {available_subcases}")
        
        # Perform comprehensive multi-condition sizing
        results = self.size_for_target_rf_multi(
            property_id=property_id,
            materials=materials,
            failure_types=failure_types,
            thickness_range=thickness_range,
            target_rf=target_rf,
            assembly_type=assembly_type
        )
        
        # Summary of results
        if results:
            print(f"\n{'='*60}")
            print(f"SIZING ANALYSIS COMPLETE")
            print(f"{'='*60}")
            
            # Find the optimum thickness (first thickness that meets target RF)
            optimum_result = None
            for result in results:
                if result['min_rf'] >= target_rf:
                    optimum_result = result
                    break
            
            if optimum_result:
                print(f"OPTIMUM DESIGN:")
                print(f"  Thickness: {optimum_result['thickness']} mm")
                print(f"  Reserve Factor: {optimum_result['min_rf']:.3f}")
                print(f"  Critical Material: {optimum_result['critical_material']}")
                print(f"  Critical Failure Type: {optimum_result['critical_failure_type']}")
                print(f"  Critical Subcase: {optimum_result['critical_subcase_id']}")
                print(f"  Critical Element: {optimum_result['critical_element']}")
            else:
                min_thickness_result = results[-1]  # Last (thickest) analyzed
                print(f"TARGET RF NOT ACHIEVED IN GIVEN RANGE")
                print(f"At maximum thickness ({min_thickness_result['thickness']} mm):")
                print(f"  Best RF achieved: {min_thickness_result['min_rf']:.3f}")
                print(f"  Critical Material: {min_thickness_result['critical_material']}")
                print(f"  Critical Failure Type: {min_thickness_result['critical_failure_type']}")
                print(f"  Critical Subcase: {min_thickness_result['critical_subcase_id']}")
                print(f"  Recommend increasing thickness range or adjusting target RF")
            
            print(f"{'='*60}")
        
        return results

    def size_for_target_rf(self, property_id, material, failure_type, 
                          thickness_range, target_rf=1.1, assembly_type="web", analyze_all_subcases=True):
        """
        Legacy single material/failure sizing function (kept for backward compatibility)
        """
        print("Warning: Using legacy single-condition sizing. Consider using rf_materialStrength for comprehensive analysis.")
        
        min_t, max_t, step_t = thickness_range
        allowable_stress = self.get_material_allowable(material)
        
        print(f"Sizing {assembly_type} assembly with {material}")
        print(f"Allowable stress: {allowable_stress} MPa")
        print(f"Target RF: {target_rf}")
        print(f"Thickness range: {min_t} to {max_t} mm, step: {step_t} mm")
        
        # Use the new multi-condition approach with single material/failure
        results = self.size_for_target_rf_multi(
            property_id=property_id,
            materials=[material],
            failure_types=[failure_type],
            thickness_range=thickness_range,
            target_rf=target_rf,
            assembly_type=assembly_type
        )
        
        return results