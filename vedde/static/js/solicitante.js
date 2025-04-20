document.addEventListener('DOMContentLoaded', function() {
    // Toast
    const toastLive = document.getElementById('liveToast');
    const toastBootstrap = bootstrap.Toast.getOrCreateInstance(toastLive);

    function showToast(message, type = 'success') {
        const icon = type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle';
        toastLive.querySelector('.toast-header i').className = `fas ${icon} me-2 text-${type}`;
        toastLive.querySelector('.toast-body').textContent = message;
        toastBootstrap.show();
    }

    // Manejar formulario principal
    const mainForm = document.getElementById('solicitanteForm');
    mainForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(mainForm);
        const submitBtn = mainForm.querySelector('button[type="submit"]');
        
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>{% trans "Guardando..." %}';

        try {
            const response = await fetch(mainForm.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            const data = await response.json();
            
            if(data.success) {
                window.location.href = data.redirect_url;
            } else {
                showToast(data.error || '{% trans "Error al guardar" %}', 'danger');
            }
        } catch (error) {
            showToast('{% trans "Error de conexión" %}', 'danger');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-save me-2"></i>{% trans "Guardar" %}';
        }
    });

    // Manejar modal de Vacante
    const vacanteForm = document.getElementById('vacanteForm');
    if(vacanteForm) {
        vacanteForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(vacanteForm);
            const submitBtn = vacanteForm.querySelector('button[type="submit"]');
            
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>{% trans "Guardando..." %}';

            try {
                const response = await fetch(vacanteForm.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });
                
                const data = await response.json();
                
                if(data.success) {
                    const select = document.getElementById('id_vacante');
                    const option = new Option(data.nombre, data.id, true, true);
                    select.add(option);
                    bootstrap.Modal.getInstance(document.getElementById('vacanteModal')).hide();
                    showToast('{% trans "Vacante creada exitosamente" %}', 'success');
                } else {
                    showToast(data.error || '{% trans "Error al crear vacante" %}', 'danger');
                }
            } catch (error) {
                showToast('{% trans "Error de conexión" %}', 'danger');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '{% trans "Crear Vacante" %}';
                vacanteForm.reset();
            }
        });
    }

    // Preview de imagen
    document.getElementById('id_foto').addEventListener('change', function(e) {
        const file = e.target.files[0];
        const preview = this.closest('.file-upload-wrapper').querySelector('.upload-preview');
        
        if(file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                preview.innerHTML = `<img src="${e.target.result}" class="img-thumbnail">`;
            };
            reader.readAsDataURL(file);
        }
    });

    // Drag and Drop
    document.querySelectorAll('.file-upload-wrapper').forEach(wrapper => {
        wrapper.addEventListener('dragover', (e) => {
            e.preventDefault();
            wrapper.style.borderColor = '#0d6efd';
        });
        
        wrapper.addEventListener('dragleave', () => {
            wrapper.style.borderColor = '#dee2e6';
        });
        
        wrapper.addEventListener('drop', (e) => {
            e.preventDefault();
            wrapper.style.borderColor = '#dee2e6';
            const file = e.dataTransfer.files[0];
            if(file) {
                const input = wrapper.querySelector('input[type="file"]');
                input.files = e.dataTransfer.files;
                input.dispatchEvent(new Event('change'));
            }
        });
    });
});