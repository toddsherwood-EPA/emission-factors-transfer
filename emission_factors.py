"""
This script reads in, from the parameters input file, the SAFE NPRM tailpipe emission factors. It also reads in, from
the OMEGA_ICBT_Inputs file used in the 2016 Proposed Determination analysis done by EPA, the tailpipe emission factors.
The script then replaces the SAFE NPRM emission factors for model years 2010 and later with those from the proposed determination
analysis. It then sets to zero, technically to NAN, the 2010 and later emission factors for the LDT2b/3 entries since EPA did not use
those in the proposed determination. If NHTSA wants to continue use of the SAFE NPRM values for 2010 and later model year LDT2b/3,
they can simply leave those columns as they were in the SAFE NPRM. The 2010 and later model year data are then appended back to the
SAFE NPRM values for 2009 and earlier - EPA did not use emission factors for 2009 and earlier so they cannot be inserted into
the SAFE format via this script. The output is two csv files, one for gasoline emission factors and one for diesel.
"""

import pandas as pd
import numpy as np
from pathlib import Path

"""
Set paths.
"""
path_cwd = Path.cwd()
path_inputs = path_cwd.joinpath('inputs')
path_safe_nprm = path_inputs.joinpath('CAFE-model-SAFE-NPRM.xlsx')
path_epa_pd = path_inputs.joinpath('OMEGA_ICBT_Inputs_PD2016.xlsx')
path_outputs = path_cwd.joinpath('outputs')

"""
Create a dictionary to rename EPA columns to NHTSA columns.
"""
header_dict = {'VOC_gpm_Car': 'LDV_VOC',
               'CO_gpm_Car': 'LDV_CO',
               'NOx_gpm_Car': 'LDV_NOx',
               'PM2.5_gpm_Car': 'LDV_PM2.5',
               'Benzene_gpm_Car': 'LDV_Benzene',
               '1,3 Butadiene_gpm_Car': 'LDV_Butadiene',
               'Formaldehyde_gpm_Car': 'LDV_Formaldehyde',
               'Acetaldehyde_gpm_Car': 'LDV_Acetaldehyde',
               'Acrolein_gpm_Car': 'LDV_Acrolein',
               'CH4_gpm_Car': 'LDV_CH4',
               'N20_gpm_Car': 'LDV_N2O',
               'SO2_gpG_Car': 'LDV_SO2',
               'VOC_gpm_Truck': 'LDT1/2a_VOC',
               'CO_gpm_Truck': 'LDT1/2a_CO',
               'NOx_gpm_Truck': 'LDT1/2a_NOx',
               'PM2.5_gpm_Truck': 'LDT1/2a_PM2.5',
               'Benzene_gpm_Truck': 'LDT1/2a_Benzene',
               '1,3 Butadiene_gpm_Truck': 'LDT1/2a_Butadiene',
               'Formaldehyde_gpm_Truck': 'LDT1/2a_Formaldehyde',
               'Acetaldehyde_gpm_Truck': 'LDT1/2a_Acetaldehyde',
               'Acrolein_gpm_Truck': 'LDT1/2a_Acrolein',
               'CH4_gpm_Truck': 'LDT1/2a_CH4',
               'N20_gpm_Truck': 'LDT1/2a_N2O',
               'SO2_gpG_Truck': 'LDT1/2a_SO2'
               }

"""
This list of columns will be set to NAN for MYs 2010 and later since EPA did not use those data in the Proposed Determination.
"""
safe_nprm_set_to_zero = ['LDT2b/3_CO', 'LDT2b/3_VOC', 'LDT2b/3_NOx', 'LDT2b/3_SO2', 'LDT2b/3_PM2.5',
                         'LDT2b/3_CO2', 'LDT2b/3_CH4', 'LDT2b/3_N2O',
                         'LDT2b/3_Acetaldehyde', 'LDT2b/3_Acrolein', 'LDT2b/3_Benzene', 'LDT2b/3_Butadiene', 'LDT2b/3_Formaldehyde',
                         'LDT2b/3_DPM10', 'LDT2b/3_MTBE']


def main():
    """Read inputs."""
    print('Reading inputs')
    gas_safe_nprm = pd.read_excel(path_safe_nprm, 'TE_Gasoline', skiprows=3)
    diesel_safe_nprm = pd.read_excel(path_safe_nprm, 'TE_Diesel', skiprows=3)
    emission_factors_pd = pd.read_excel(path_epa_pd, 'Vehicle_EFs')

    """Rename EPA metrics to NHTSA naming."""
    for key, value in header_dict.items(): emission_factors_pd.rename(columns={key: value}, inplace=True)

    """Make some adjustments to the EPA data - split ID column into MY and Age. Set Age to be consistent with NHTSA use of 1-40 rather than 0-39."""
    my_age = emission_factors_pd['ID'].str.split('-', expand=True)
    my_age.rename(columns={0: 'ModelYear'}, inplace=True)
    my_age.rename(columns={1: 'Age'}, inplace=True)
    my_age['ModelYear'] = pd.to_numeric(my_age['ModelYear'])
    my_age['Age'] = pd.to_numeric(my_age['Age'])
    my_age['Age'] = my_age['Age'] + 1
    emission_factors_pd = my_age.join(emission_factors_pd)
    emission_factors_pd.drop(labels='ID', axis=1, inplace=True)
    pd_minMY = emission_factors_pd['ModelYear'].min()
    metrics = emission_factors_pd.columns.tolist()[2:]

    """Create new dataframes that consist of MY 2010 and later data."""
    gas_safe = pd.DataFrame(gas_safe_nprm.loc[gas_safe_nprm['ModelYear'] >= pd_minMY])
    diesel_safe = pd.DataFrame(diesel_safe_nprm.loc[diesel_safe_nprm['ModelYear'] >= pd_minMY])
    gas_safe.index = range(0, len(gas_safe))
    diesel_safe.index = range(0, len(diesel_safe))

    """Set metrics to equal EPA data."""
    print('Transferring EPA data into NHTSA file.')
    for metric in metrics:
        gas_safe[metric] = emission_factors_pd[metric]
        diesel_safe[metric] = emission_factors_pd[metric]

    for metric in safe_nprm_set_to_zero:
        gas_safe[metric] = np.nan
        diesel_safe[metric] = np.nan

    """Create new dataframes consisting of SAFE NPRM data for MYs 2009 and earlier, then append new MY 2010 and later data."""
    gas_safe_nprm = pd.DataFrame(gas_safe_nprm.loc[gas_safe_nprm['ModelYear'] < pd_minMY])
    diesel_safe_nprm = pd.DataFrame(diesel_safe_nprm.loc[diesel_safe_nprm['ModelYear'] < pd_minMY])
    gas_safe = gas_safe_nprm.append(gas_safe)
    diesel_safe = diesel_safe_nprm.append(diesel_safe)

    """Create output folder if it doesn't already exist and save outputs to it."""
    print('Saving outputs into the outputs folder.')
    path_outputs.mkdir(exist_ok=True)
    gas_safe.to_csv(path_outputs.joinpath('TE_Gasoline.csv'), index=False)
    diesel_safe.to_csv(path_outputs.joinpath('TE_Diesel.csv'), index=False)

    input('Press Enter to Exit....')
    exit()


if __name__ == '__main__':
    main()
