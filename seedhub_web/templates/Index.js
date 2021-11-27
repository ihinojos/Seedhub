function ChangeTitleModal(type){
    console.log(type)
    if(type === 'add'){
        document.getElementById('titleModal').textContent = "AGREGAR PLANTA"
        document.getElementById('buttonModal').textContent = "AÑADIR"
    } else {
        document.getElementById('titleModal').textContent = "EDITAR PLANTA"
        document.getElementById('buttonModal').textContent = "EDITAR"
    }
}