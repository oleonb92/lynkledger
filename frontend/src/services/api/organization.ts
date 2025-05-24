import api from './axios';

export interface UpdateOrganizationData {
  name?: string;
  type?: string;
  description?: string;
}

export interface InviteMemberData {
  email: string;
  role: string;
  message?: string;
}

export const updateOrganization = async (organizationId: number, data: UpdateOrganizationData) => {
  const response = await api.put(`/organizations/${organizationId}/`, data);
  return response.data;
};

export const getOrganizationMembers = async (organizationId: number) => {
  const response = await api.get(`/organizations/${organizationId}/members/`);
  return response.data;
};

export const updateMemberRole = async (organizationId: number, memberId: number, role: string) => {
  const response = await api.put(`/organizations/${organizationId}/members/${memberId}/`, { role });
  return response.data;
};

export const removeMember = async (organizationId: number, memberId: number) => {
  const response = await api.delete(`/organizations/${organizationId}/members/${memberId}/`);
  return response.data;
};

export const getOrganizationInvitations = async () => {
  const response = await api.get(`/invitations/`);
  return response.data;
};

export const inviteMember = async (organizationId: number, data: InviteMemberData) => {
  const response = await api.post(`/organizations/${organizationId}/invite/`, data);
  return response.data;
};

export const cancelInvitation = async (invitationToken: string) => {
  const response = await api.delete(`/invitations/${invitationToken}/`);
  return response.data;
};

export const resendInvitation = async (invitationToken: string) => {
  const response = await api.post(`/invitations/${invitationToken}/resend/`);
  return response.data;
};

export const generateMagicLink = async (organizationId: number) => {
  const response = await api.post(`/organizations/${organizationId}/magic-link/`);
  return response.data;
};

export const getOrganization = async (organizationId: number) => {
  const response = await api.get(`/organizations/${organizationId}/`);
  return response.data;
}; 