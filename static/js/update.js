//so this is the tricky part, actually I wanted to have an admin page from where I can control the order and user data easily and also be able to edit them,
// now the problem is dont want to use heavy javascript or have more html pages or function so I decided on a simple table and an edit button to have a modal section
// that will submit a form in post method so that I can edit the database based on the input and I didn't knew that there is an option in the javascript event's named 'show.bs.modal'
// so honestly this is the part of the code or this is peice of code that has been heavily worked taken from google, also I took a lot of AI help to get this right and working,
// though I have understanding of the code, what I have written and why I have written, but the fact is I would never new about it without AI telling me that there is also a way.

document.addEventListener('DOMContentLoaded', () => {
    const editModal = document.getElementById('edit');

    if (editModal) {
        editModal.addEventListener('show.bs.modal', (e) => {
            const button = e.relatedTarget;

            document.getElementById('modalUserInfo').textContent = button
                .getAttribute('data-user-info');
            document.getElementById('modalOrderInfo').textContent = '#ORD-' + button
                .getAttribute('data-order-id');
            document.getElementById('modalOrderId').value = button.getAttribute(
                'data-order-id');
            document.getElementById('modalStatus').value = button.getAttribute(
                'data-status');
            document.getElementById('modalCategory').value = button.getAttribute(
                'data-category');
            document.getElementById('modalRate').value = button.getAttribute(
                'data-rate');
            document.getElementById('modalWeight').value = button.getAttribute(
                'data-weight');
            document.getElementById('modalSettled').value = button.getAttribute(
                'data-settled');
        });
    }
});
