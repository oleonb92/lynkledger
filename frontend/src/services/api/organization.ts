import api from './axios';

// Obtener miembros de la organización
export const getOrganizationMembers = (orgId: string | number) =>
  api.get(`/organizations/${orgId}/members`);

// Obtener invitaciones de la organización
export const getOrganizationInvitations = () =>
  api.get('/invitations');

// Invitar miembro
export const inviteMember = (orgId: string | number, data: { email: string; role: string; message?: string }) =>
  api.post('/invitations', { ...data, organization: orgId });

// Cambiar rol de miembro
export const updateMemberRole = (membershipId: string | number, role: string) =>
  api.patch(`/memberships/${membershipId}`, { role });

// Remover miembro
export const removeMember = (membershipId: string | number) =>
  api.delete(`/memberships/${membershipId}`);

// Reenviar invitación (puedes reutilizar inviteMember con el mismo email)
// Cancelar invitación
export const cancelInvitation = (invitationId: string | number) =>
  api.delete(`/invitations/${invitationId}`); 