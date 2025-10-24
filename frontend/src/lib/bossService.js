import api from './api';

const BOSS_BASE_URL = '/bosses';

export const getBosses = async (params) => {
  try {
    const response = await api.get(BOSS_BASE_URL, { params: params });
    return response.data;
  } catch (error) {
    console.error("Error fetching bosses:", error);
    throw error;
  }
};