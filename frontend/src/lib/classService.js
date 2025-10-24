import api from './api';

const CLASS_BASE_URL = '/classes';

export const getClasses = async (params) => {
  try {
    const response = await api.get(CLASS_BASE_URL, { params });
    return response.data;
  } catch (error) {
    console.error("Error fetching classes:", error);
    throw error;
  }
};
