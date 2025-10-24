import api from './api';

const ARMOR_BASE_URL = '/armors';

export const getArmors = async (params) => {
  try {
    const response = await api.get(ARMOR_BASE_URL, { params: params });
    return response.data;
  } catch (error) {
    console.error("Error fetching armors:", error);
    throw error;
  }
};