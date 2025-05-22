import React, { useEffect, useState } from 'react';
import { Box, Grid, Typography, Avatar, Button, TextField, Chip, Snackbar, CircularProgress } from '@mui/material';
import { getOrganizationMembers, getOrganizationInvitations, inviteMember } from '../services/api/organization';
import CardContainer from '../components/common/CardContainer';
import { useAppSelector } from '../store';
// import { motion } from 'framer-motion';

const Profile: React.FC = () => {
  console.log("Profile component mounted");
  const { user } = useAppSelector((state) => state.auth);
  console.log("Estado del usuario en Profile:", user);
  
  const [members, setMembers] = useState<any[]>([]);
  const [invitations, setInvitations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('member');
  const [inviteMsg, setInviteMsg] = useState('');
  const [snackbar, setSnackbar] = useState<{open: boolean, message: string, severity?: 'success'|'error'}>({open: false, message: ''});

  useEffect(() => {
    const fetchData = async () => {
      console.log("Fetching data with organizationId:", user?.organizationId);
      if (!user?.organizationId) {
        console.log("No organizationId found in user state");
        setSnackbar({open: true, message: 'No tienes una organización asignada', severity: 'error'});
        setLoading(false);
        return;
      }

      setLoading(true);
      try {
        const [membersRes, invitationsRes] = await Promise.all([
          getOrganizationMembers(user.organizationId),
          getOrganizationInvitations()
        ]);
        setMembers(membersRes.data);
        setInvitations(invitationsRes.data);
      } catch (err: any) {
        console.error('Error fetching data:', err);
        setSnackbar({
          open: true, 
          message: err?.response?.data?.detail || 'Error cargando datos', 
          severity: 'error'
        });
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [user?.organizationId]);

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user?.organizationId) {
      setSnackbar({
        open: true,
        message: 'No tienes una organización asignada',
        severity: 'error'
      });
      return;
    }

    try {
      await inviteMember(user.organizationId, { 
        email: inviteEmail, 
        role: inviteRole, 
        message: inviteMsg 
      });
      setSnackbar({open: true, message: 'Invitación enviada', severity: 'success'});
      setInviteEmail('');
      setInviteMsg('');
      // Refrescar invitaciones
      const invitationsRes = await getOrganizationInvitations();
      setInvitations(invitationsRes.data);
    } catch (err: any) {
      console.error('Error sending invitation:', err);
      setSnackbar({
        open: true, 
        message: err?.response?.data?.detail || 'Error enviando invitación', 
        severity: 'error'
      });
    }
  };

  return (
    <Box sx={{ minHeight: '100vh', p: { xs: 2, md: 6 }, background: theme => theme.palette.background.default }}>
      <Grid container spacing={4} justifyContent="center" alignItems="flex-start">
        {/* Fila superior: Perfil y Organización */}
        <Grid item xs={12} md={4}>
          <CardContainer>
            <Box display="flex" flexDirection="column" alignItems="center">
              <Avatar sx={{ width: 80, height: 80, mb: 2 }} />
              <Typography variant="h6" color="white">Nombre Apellido</Typography>
              <Typography variant="body2" color="#A0A4B8">usuario@email.com</Typography>
              <Button variant="outlined" sx={{ mt: 2 }}>Editar perfil</Button>
            </Box>
          </CardContainer>
        </Grid>
        <Grid item xs={12} md={8}>
          <CardContainer>
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <Typography variant="h6" color="white">Leon's Family</Typography>
                <Chip label="Household" color="primary" sx={{ mt: 1 }} />
              </Box>
              <Button variant="outlined">Editar organización</Button>
            </Box>
          </CardContainer>
        </Grid>
        {/* Fila inferior: Miembros, Invitaciones, Formulario */}
        <Grid item xs={12} md={12}>
          <Box display="flex" flexDirection="column" gap={4}>
            {/* Card Miembros */}
            <CardContainer>
              <Typography variant="h6" color="white" mb={2}>Miembros</Typography>
              {loading ? <CircularProgress color="primary" /> : (
                <Box display="flex" gap={2} flexWrap="wrap">
                  {members.map((member) => (
                    <Box key={member.id} display="flex" alignItems="center" gap={1} sx={{ background: 'rgba(255,255,255,0.04)', borderRadius: 2, p: 1.5 }}>
                      <Avatar sx={{ width: 40, height: 40 }} />
                      <Box>
                        <Typography color="white">{member.user_full_name}</Typography>
                        <Chip label={member.role} color="secondary" size="small" />
                      </Box>
                      <Button size="small" variant="text" sx={{ ml: 1 }}>Cambiar rol</Button>
                      <Button size="small" variant="text" color="error">Remover</Button>
                    </Box>
                  ))}
                </Box>
              )}
            </CardContainer>
            {/* Card Invitaciones */}
            <CardContainer>
              <Typography variant="h6" color="white" mb={2}>Invitaciones pendientes</Typography>
              {loading ? <CircularProgress color="primary" /> : (
                <Box display="flex" gap={2} flexWrap="wrap">
                  {invitations.map((inv) => (
                    <Box key={inv.id} display="flex" alignItems="center" gap={1} sx={{ background: 'rgba(255,255,255,0.04)', borderRadius: 2, p: 1.5 }}>
                      <Typography color="white">{inv.email}</Typography>
                      <Chip label={inv.status} color="warning" size="small" />
                      <Button size="small" variant="text">Reenviar</Button>
                      <Button size="small" variant="text" color="error">Cancelar</Button>
                    </Box>
                  ))}
                </Box>
              )}
            </CardContainer>
            {/* Card Formulario de invitación */}
            <CardContainer>
              <Typography variant="h6" color="white" mb={2}>Invitar miembro</Typography>
              <Box component="form" display="flex" gap={2} alignItems="center" onSubmit={handleInvite}>
                <TextField label="Email" variant="filled" value={inviteEmail} onChange={e => setInviteEmail(e.target.value)} sx={{ input: { color: 'white' }, background: 'rgba(255,255,255,0.04)' }} />
                <TextField label="Rol" variant="filled" select SelectProps={{ native: true }} value={inviteRole} onChange={e => setInviteRole(e.target.value)} sx={{ minWidth: 120, background: 'rgba(255,255,255,0.04)' }}>
                  <option value="member">Miembro</option>
                  <option value="admin">Admin</option>
                  <option value="viewer">Viewer</option>
                </TextField>
                <TextField label="Mensaje" variant="filled" value={inviteMsg} onChange={e => setInviteMsg(e.target.value)} sx={{ input: { color: 'white' }, background: 'rgba(255,255,255,0.04)' }} />
                <Button variant="contained" color="primary" type="submit">Invitar</Button>
              </Box>
            </CardContainer>
            {/* Card Link mágico */}
            <CardContainer>
              <Typography variant="h6" color="white" mb={2}>Link mágico de invitación</Typography>
              <Box display="flex" alignItems="center" gap={2}>
                <TextField value="https://lynkledger-frontend.vercel.app/accept-invite/1234abcd" variant="filled" InputProps={{ readOnly: true, style: { color: 'white' } }} sx={{ flex: 1, background: 'rgba(255,255,255,0.04)' }} />
                <Button variant="outlined">Copiar</Button>
                <Button variant="outlined" color="success">QR</Button>
                <Button variant="outlined" color="secondary">WhatsApp</Button>
              </Box>
            </CardContainer>
          </Box>
        </Grid>
      </Grid>
      <Snackbar open={snackbar.open} autoHideDuration={4000} onClose={() => setSnackbar({ ...snackbar, open: false })} message={snackbar.message} />
    </Box>
  );
};

export default Profile; 