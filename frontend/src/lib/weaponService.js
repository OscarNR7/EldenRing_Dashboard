import api from './api';

const WEAPON_BASE_URL = '/weapons';

export const getWeapons = async (params) => {
  try {
    const response = await api.get(WEAPON_BASE_URL, { params: params });
    return response.data;
  } catch (error) {
    console.error("Error fetching weapons:", error);
    throw error;
  }
};

export const getWeaponCategories = async () => {
  try {
    const response = await api.get(`${WEAPON_BASE_URL}/categories`);
    return response.data;
  } catch (error) {
    console.error("Error fetching weapon categories:", error);
    throw error;
  }
};

export const getWeaponStatistics = async () => {
  try {
    const response = await api.get(`${WEAPON_BASE_URL}/statistics`);
    return response.data;
  } catch (error) {
    console.error("Error fetching weapon statistics:", error);
    throw error;
  }
};

export const compareWeapons = async (weaponIds) => {
  try {
    const response = await api.post(`${WEAPON_BASE_URL}/compare`, { weapon_ids: weaponIds });
    return response.data;
  } catch (error) {
    console.error("Error comparing weapons:", error);
    throw error;
  }
};

export const getWeaponsByBuild = async (buildType) => {
  try {
    const response = await api.get(`${WEAPON_BASE_URL}/by-build/${buildType}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching weapons by build type ${buildType}:`, error);
    throw error;
  }
};