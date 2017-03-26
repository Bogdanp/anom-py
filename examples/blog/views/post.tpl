% if not embedded:
  % rebase("template.tpl", title=post.title)
% end

<div class="row">
    <div class="col-12">
    <h4><a href="/posts/{{ post.slug }}">{{ post.title }}</a></h4>
    <h5>Posted on <em>{{ post.created_at }}</em></h5>
    % if post.tags:
    <h6>
      Tags:

      % for tag in post.tags:
      <a href="/?tag={{ tag }}">{{ tag }}</a>
      % end
    </h6>
    % end
    <p>{{ !post.body_markdown }}</p>
    <hr/>
    </div>
</div>
