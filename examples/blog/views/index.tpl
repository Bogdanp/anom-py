% rebase("template.tpl", title="Posts")

<div class="row">
  <div class="col-9">
    % for post in pages.fetch_next_page():
      % include("post.tpl", post=post, embedded=True)
    % end

    % if pages.has_more:
    <a href="/?cursor={{ pages.cursor }}" class="btn btn-primary">Next page</a>
    % end
  </div>

  <div class="col-3" style="background: #F9F9F9; padding: 1em">
    % if "create" in user.permissions:
      <a href="/new" class="btn">New post</a>
    % end
  </div>
</div>
