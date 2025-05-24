import React, { useEffect, useState } from 'react';
import { Box, Grid, Typography, Avatar, Button, TextField, Chip, Snackbar, CircularProgress, Dialog, DialogTitle, DialogContent, DialogActions, MenuItem, IconButton } from '@mui/material';
import { getOrganizationMembers, getOrganizationInvitations, inviteMember, cancelInvitation, resendInvitation, updateOrganization, updateMemberRole, removeMember, generateMagicLink, getOrganization } from '../services/api/organization';
import { getProfile, updateProfile, UpdateProfileData } from '../services/api/user';
import CardContainer from '../components/common/CardContainer';
import { useAppSelector } from '../store';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import QrCodeIcon from '@mui/icons-material/QrCode';
import WhatsAppIcon from '@mui/icons-material/WhatsApp';

const Profile: React.FC = () => {
  const { user } = useAppSelector((state) => state.auth);
  
  const [profile, setProfile] = useState<any>(null);
  const [members, setMembers] = useState<any[]>([]);
  const [invitations, setInvitations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('member');
  const [inviteMsg, setInviteMsg] = useState('');
  const [snackbar, setSnackbar] = useState<{open: boolean, message: string, severity?: 'success'|'error'}>({open: false, message: ''});
  
  // Estados para diálogos
  const [editProfileOpen, setEditProfileOpen] = useState(false);
  const [editOrgOpen, setEditOrgOpen] = useState(false);
  const [qrDialogOpen, setQrDialogOpen] = useState(false);
  const [magicLink, setMagicLink] = useState('');
  
  // Estados para formularios
  const [editProfileData, setEditProfileData] = useState<UpdateProfileData>({});
  const [editOrgData, setEditOrgData] = useState({ name: '', type: '', description: '' });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [organization, setOrganization] = useState<any>(null);

  useEffect(() => {
    const fetchData = async () => {
      if (!user?.organizationId) {
        setSnackbar({open: true, message: 'No tienes una organización asignada', severity: 'error'});
        setLoading(false);
        return;
      }

      setLoading(true);
      try {
        const [profileRes, membersRes, invitationsRes, orgRes] = await Promise.all([
          getProfile(),
          getOrganizationMembers(user.organizationId),
          getOrganizationInvitations(),
          getOrganization(user.organizationId)
        ]);
        setProfile(profileRes);
        setMembers(membersRes);
        setInvitations(invitationsRes);
        setOrganization(orgRes);
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
      const invitationsRes = await getOrganizationInvitations();
      setInvitations(invitationsRes);
    } catch (err: any) {
      setSnackbar({
        open: true, 
        message: err?.response?.data?.detail || 'Error enviando invitación', 
        severity: 'error'
      });
    }
  };

  const handleResend = async (invitation: any) => {
    try {
      await resendInvitation(invitation.token);
      setSnackbar({ open: true, message: 'Invitación reenviada', severity: 'success' });
      const invitationsRes = await getOrganizationInvitations();
      setInvitations(invitationsRes);
    } catch (err: any) {
      setSnackbar({ open: true, message: 'Error al reenviar invitación', severity: 'error' });
    }
  };

  const handleCancel = async (invitation: any) => {
    try {
      await cancelInvitation(invitation.token);
      setSnackbar({ open: true, message: 'Invitación cancelada', severity: 'success' });
      const invitationsRes = await getOrganizationInvitations();
      setInvitations(invitationsRes);
    } catch (err: any) {
      setSnackbar({ open: true, message: 'Error al cancelar invitación', severity: 'error' });
    }
  };

  const handleUpdateProfile = async () => {
    try {
      const data = { ...editProfileData };
      if (selectedFile) {
        data.avatar = selectedFile;
      }
      const updatedProfile = await updateProfile(data);
      setProfile(updatedProfile);
      setEditProfileOpen(false);
      setSnackbar({ open: true, message: 'Perfil actualizado', severity: 'success' });
    } catch (err: any) {
      setSnackbar({ open: true, message: 'Error al actualizar perfil', severity: 'error' });
    }
  };

  const handleUpdateOrganization = async () => {
    try {
      if (!user?.organizationId) return;
      await updateOrganization(user.organizationId, editOrgData);
      setEditOrgOpen(false);
      setSnackbar({ open: true, message: 'Organización actualizada', severity: 'success' });
    } catch (err: any) {
      setSnackbar({ open: true, message: 'Error al actualizar organización', severity: 'error' });
    }
  };

  const handleUpdateMemberRole = async (memberId: number, newRole: string) => {
    try {
      if (!user?.organizationId) return;
      await updateMemberRole(user.organizationId, memberId, newRole);
      const membersRes = await getOrganizationMembers(user.organizationId);
      setMembers(membersRes);
      setSnackbar({ open: true, message: 'Rol actualizado', severity: 'success' });
    } catch (err: any) {
      setSnackbar({ open: true, message: 'Error al actualizar rol', severity: 'error' });
    }
  };

  const handleRemoveMember = async (memberId: number) => {
    try {
      if (!user?.organizationId) return;
      await removeMember(user.organizationId, memberId);
      const membersRes = await getOrganizationMembers(user.organizationId);
      setMembers(membersRes);
      setSnackbar({ open: true, message: 'Miembro removido', severity: 'success' });
    } catch (err: any) {
      setSnackbar({ open: true, message: 'Error al remover miembro', severity: 'error' });
    }
  };

  const handleGenerateMagicLink = async () => {
    try {
      if (!user?.organizationId) return;
      const response = await generateMagicLink(user.organizationId);
      setMagicLink(response.magic_link);
    } catch (err: any) {
      setSnackbar({ open: true, message: 'Error al generar link mágico', severity: 'error' });
    }
  };

  const handleCopyLink = () => {
    navigator.clipboard.writeText(magicLink);
    setSnackbar({ open: true, message: 'Link copiado al portapapeles', severity: 'success' });
  };

  const handleShareWhatsApp = () => {
    const text = `¡Únete a mi organización en LynkLedger! ${magicLink}`;
    window.open(`https://wa.me/?text=${encodeURIComponent(text)}`);
  };

  // Función para obtener iniciales
  function getInitials(name: string, lastName: string) {
    if (!name && !lastName) return '';
    return `${name?.[0] || ''}${lastName?.[0] || ''}`.toUpperCase();
  }

  return (
    <Box sx={{ minHeight: '100vh', p: { xs: 2, md: 6 }, background: theme => theme.palette.background.default }}>
      <Grid container spacing={4} justifyContent="center" alignItems="flex-start">
        {/* Fila superior: Perfil y Organización */}
        <Grid item xs={12} md={4}>
          <CardContainer>
            <Box display="flex" flexDirection="column" alignItems="center">
              <Avatar 
                src={profile?.avatar || undefined} 
                sx={{ width: 80, height: 80, mb: 2, bgcolor: 'primary.main', color: 'white', fontSize: 36 }}
              >
                {!profile?.avatar && getInitials(profile?.first_name, profile?.last_name)}
              </Avatar>
              <Typography variant="h6" color="white">
                {profile?.first_name} {profile?.last_name}
              </Typography>
              <Typography variant="body2" color="#A0A4B8">{profile?.email}</Typography>
              <Button 
                variant="outlined" 
                sx={{ mt: 2 }}
                onClick={() => setEditProfileOpen(true)}
              >
                Editar perfil
              </Button>
            </Box>
          </CardContainer>
        </Grid>
        <Grid item xs={12} md={8}>
          <CardContainer>
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <Chip label={organization?.name || ''} color="primary" sx={{ mt: 1, fontSize: '1.2rem', height: 40, minWidth: 120, px: 2, fontWeight: 600 }} />
              </Box>
              <Button 
                variant="outlined"
                onClick={() => setEditOrgOpen(true)}
              >
                Editar organización
              </Button>
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
                      <Avatar src={member.avatar} sx={{ width: 40, height: 40 }} />
                      <Box>
                        <Typography color="white">{member.user_full_name}</Typography>
                        <Chip label={member.role} color="secondary" size="small" />
                      </Box>
                      <TextField
                        select
                        size="small"
                        value={member.role}
                        onChange={(e) => handleUpdateMemberRole(member.id, e.target.value)}
                        sx={{ minWidth: 120, ml: 1 }}
                      >
                        <MenuItem value="owner">Owner</MenuItem>
                        <MenuItem value="admin">Admin</MenuItem>
                        <MenuItem value="manager">Manager</MenuItem>
                        <MenuItem value="accountant">Accountant</MenuItem>
                        <MenuItem value="bookkeeper">Bookkeeper</MenuItem>
                        <MenuItem value="member">Miembro</MenuItem>
                        <MenuItem value="viewer">Viewer</MenuItem>
                      </TextField>
                      <Button 
                        size="small" 
                        variant="text" 
                        color="error"
                        onClick={() => handleRemoveMember(member.id)}
                      >
                        Remover
                      </Button>
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
                      <Button 
                        size="small" 
                        variant="text" 
                        onClick={() => handleResend(inv)} 
                        sx={{ color: '#00bcd4' }}
                      >
                        Reenviar
                      </Button>
                      <Button 
                        size="small" 
                        variant="text" 
                        color="error" 
                        onClick={() => handleCancel(inv)}
                      >
                        Cancelar
                      </Button>
                    </Box>
                  ))}
                </Box>
              )}
            </CardContainer>

            {/* Card Formulario de invitación */}
            <CardContainer>
              <Typography variant="h6" color="white" mb={2}>Invitar miembro</Typography>
              <Box component="form" display="flex" gap={2} alignItems="center" onSubmit={handleInvite}>
                <TextField 
                  label="Email" 
                  variant="filled" 
                  value={inviteEmail} 
                  onChange={e => setInviteEmail(e.target.value)} 
                  sx={{ input: { color: 'white' }, background: 'rgba(255,255,255,0.04)' }} 
                />
                <TextField 
                  label="Rol" 
                  variant="filled" 
                  select 
                  SelectProps={{ native: true }} 
                  value={inviteRole} 
                  onChange={e => setInviteRole(e.target.value)} 
                  sx={{ minWidth: 120, background: 'rgba(255,255,255,0.04)' }}
                >
                  <option value="member">Miembro</option>
                  <option value="admin">Admin</option>
                  <option value="viewer">Viewer</option>
                </TextField>
                <TextField 
                  label="Mensaje" 
                  variant="filled" 
                  value={inviteMsg} 
                  onChange={e => setInviteMsg(e.target.value)} 
                  sx={{ input: { color: 'white' }, background: 'rgba(255,255,255,0.04)' }} 
                />
                <Button variant="contained" color="primary" type="submit">Invitar</Button>
              </Box>
            </CardContainer>

            {/* Card Link mágico */}
            <CardContainer>
              <Typography variant="h6" color="white" mb={2}>Link mágico de invitación</Typography>
              <Box display="flex" alignItems="center" gap={2}>
                <TextField 
                  value={magicLink || 'Genera un link mágico para invitar miembros'} 
                  variant="filled" 
                  InputProps={{ readOnly: true, style: { color: 'white' } }} 
                  sx={{ flex: 1, background: 'rgba(255,255,255,0.04)' }} 
                />
                <Button 
                  variant="outlined" 
                  onClick={handleGenerateMagicLink}
                >
                  Generar
                </Button>
                <IconButton 
                  color="primary" 
                  onClick={handleCopyLink}
                  disabled={!magicLink}
                >
                  <ContentCopyIcon />
                </IconButton>
                <IconButton 
                  color="primary" 
                  onClick={() => setQrDialogOpen(true)}
                  disabled={!magicLink}
                >
                  <QrCodeIcon />
                </IconButton>
                <IconButton 
                  color="success" 
                  onClick={handleShareWhatsApp}
                  disabled={!magicLink}
                >
                  <WhatsAppIcon />
                </IconButton>
              </Box>
            </CardContainer>
          </Box>
        </Grid>
      </Grid>

      {/* Diálogo de edición de perfil */}
      <Dialog open={editProfileOpen} onClose={() => setEditProfileOpen(false)}>
        <DialogTitle>Editar Perfil</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} sx={{ mt: 2 }}>
            <TextField
              label="Nombre"
              value={editProfileData.first_name || ''}
              onChange={(e) => setEditProfileData({ ...editProfileData, first_name: e.target.value })}
            />
            <TextField
              label="Apellido"
              value={editProfileData.last_name || ''}
              onChange={(e) => setEditProfileData({ ...editProfileData, last_name: e.target.value })}
            />
            <TextField
              label="Email"
              value={editProfileData.email || ''}
              onChange={(e) => setEditProfileData({ ...editProfileData, email: e.target.value })}
            />
            <Button
              variant="outlined"
              component="label"
            >
              Cambiar Avatar
              <input
                type="file"
                hidden
                accept="image/*"
                onChange={(e) => {
                  if (e.target.files?.[0]) {
                    setSelectedFile(e.target.files[0]);
                  }
                }}
              />
            </Button>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditProfileOpen(false)}>Cancelar</Button>
          <Button onClick={handleUpdateProfile} variant="contained">Guardar</Button>
        </DialogActions>
      </Dialog>

      {/* Diálogo de edición de organización */}
      <Dialog open={editOrgOpen} onClose={() => setEditOrgOpen(false)}>
        <DialogTitle>Editar Organización</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} sx={{ mt: 2 }}>
            <TextField
              label="Nombre"
              value={editOrgData.name}
              onChange={(e) => setEditOrgData({ ...editOrgData, name: e.target.value })}
            />
            <TextField
              label="Tipo"
              select
              value={editOrgData.type}
              onChange={(e) => setEditOrgData({ ...editOrgData, type: e.target.value })}
            >
              <MenuItem value="household">Household</MenuItem>
              <MenuItem value="business">Business</MenuItem>
              <MenuItem value="other">Other</MenuItem>
            </TextField>
            <TextField
              label="Descripción"
              multiline
              rows={4}
              value={editOrgData.description}
              onChange={(e) => setEditOrgData({ ...editOrgData, description: e.target.value })}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditOrgOpen(false)}>Cancelar</Button>
          <Button onClick={handleUpdateOrganization} variant="contained">Guardar</Button>
        </DialogActions>
      </Dialog>

      {/* Diálogo de QR */}
      <Dialog open={qrDialogOpen} onClose={() => setQrDialogOpen(false)}>
        <DialogTitle>QR Code</DialogTitle>
        <DialogContent>
          <Box display="flex" justifyContent="center" p={2}>
            {magicLink && (
              <img 
                src={`https://chart.googleapis.com/chart?cht=qr&chs=256x256&chl=${encodeURIComponent(magicLink)}`}
                alt="QR Code"
                style={{ width: 256, height: 256 }}
              />
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setQrDialogOpen(false)}>Cerrar</Button>
        </DialogActions>
      </Dialog>

      <Snackbar 
        open={snackbar.open} 
        autoHideDuration={4000} 
        onClose={() => setSnackbar({ ...snackbar, open: false })} 
        message={snackbar.message} 
      />
    </Box>
  );
};

export default Profile; 