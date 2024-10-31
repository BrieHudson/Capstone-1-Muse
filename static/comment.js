document.querySelectorAll('.comment-btn').forEach(button => {
    button.addEventListener('click', function() {
        const postId = this.getAttribute('data-post-id');  // Access the post.id value
        toggleCommentForm(postId);  // Pass the post.id to the function
    });
});

function toggleCommentForm(postId) {
    console.log('Toggling comment form for post ID:', postId);
    const commentForm = document.getElementById(`comment-form-${postId}`);
    if (commentForm.style.display === 'none') {
        commentForm.style.display = 'block';
    } else {
        commentForm.style.display = 'none';
    }
}
