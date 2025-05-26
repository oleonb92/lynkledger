import api from './axios';

export interface UpdateProfileData {
  first_name?: string;
  last_name?: string;
  email?: string;
  avatar?: File;
}

export const updateProfile = async (data: UpdateProfileData) => {
  const formData = new FormData();
  Object.entries(data).forEach(([key, value]) => {
    if (value !== undefined) {
      formData.append(key, value);
    }
  });

  const response = await api.put(`/profile/`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getProfile = async () => {
  const response = await api.get(`/profile/`);
  return response.data;
}; 