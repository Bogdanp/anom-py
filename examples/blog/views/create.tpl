% rebase("template.tpl", title="New Post")

<div class="row">
  <div class="col-12">
    <h3>New post</h3>

    <form action="" method="POST" charset="utf-8">
      <div class="form-group">
        <label for="title">Title:</label>
        <input type="text" id="title" name="title" class="form-control">
      </div>
      <div class="form-group">
        <label for="tags">Tags:</label>
        <input type="text" id="tags" name="tags" class="form-control">
      </div>
      <div class="form-group">
        <label for="body">Body:</label>
        <textarea id="body" name="body" rows="20" class="form-control"></textarea>
      </div>
      <button type="submit" class="btn btn-primary">Post</button>
    </form>
  </div>
</div>
