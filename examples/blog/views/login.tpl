% rebase("template.tpl", title="Login")

<div class="row">
  <div class="col-6 offset-3">
    <h1>Login</h1>

    % if defined("error"):
    <div class="alert alert-danger" role="alert">
      <strong>Error!</strong> {{error}}
    </div>
    % end

    <form action="" method="post">
      <div class="form-group">
        <label for="username">Username</label>
        <input type="text" id="username" name="username" class="form-control">
      </div>
      <div class="form-group">
        <label for="password">Password</label>
        <input type="password" id="password" name="password" class="form-control">
      </div>
      <button type="submit" class="btn btn-primary">Login</button>
    </form>
  </div>
</div>
