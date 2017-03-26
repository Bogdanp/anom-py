<!doctype html>
<html lang="en-us">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">

    <title>Guestbook Example</title>

    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0-alpha.6/css/bootstrap.min.css" integrity="sha384-rwoIResjU2yc3z8GV/NPeZWAv56rSmLldC3R/AZzGRnGxQQKnKkoFVhFQhNUwEyJ" crossorigin="anonymous">
  </head>
  <body>
    <div class="container">
      <h1>Guestbook</h1>
      <br/>

      <div class="row">
        <div class="col-4">
          <h4>Sign guestbook</h4>
          <br/>

          <form action="/sign" method="POST">
            <div class="form-group">
              <label for="author">Name:</label>
              <input id="author" name="author" class="form-control" />
            </div>
            <div class="form-group">
              <label for="message">Message:</label>
              <textarea id="message" name="message" rows="8" class="form-control"></textarea>
            </div>
            <button type="submit" class="btn btn-primary">Sign guestbook</button>
          </form>
        </div>

        <div class="col-8">
          <h4>Entries:</h4>
          <br/>

          % for entry in pages.fetch_next_page():
          <div class="row">
            <div class="col-12">
              <p>{{entry.message}}</p>
              <hr>
              <form action="/delete/{{entry.key.int_id}}" method="POST">
                <h6>
                  Signed by <strong>{{entry.author or 'anonymous'}}</strong> on <em>{{entry.created_at}}</em>.

                  <button type="submit" onclick="return confirm('Are you sure?');" class="btn btn-danger btn-sm">
                    Delete
                  </button>
                </h6>
              </form>
            </div>
          </div>
          % end

          % if pages.has_more:
          <div class="row">
            <div class="col-12">
              <hr>
              <a href="/?cursor={{pages.cursor}}" class="btn btn-secondary btn-sm">Next page</a>
            </div>
          </div>
          % end
        </div>
      </div>
    </div>

    <script src="https://code.jquery.com/jquery-3.1.1.slim.min.js" integrity="sha384-A7FZj7v+d/sdmMqp/nOQwliLvUsJfDHW+k9Omg/a/EheAdgtzNs3hpfag6Ed950n" crossorigin="anonymous"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/tether/1.4.0/js/tether.min.js" integrity="sha384-DztdAPBWPRXSA/3eYEEUWrWCy7G5KFbe8fFjk5JAIxUYHKkDx6Qin1DkWx51bBrb" crossorigin="anonymous"></script>
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0-alpha.6/js/bootstrap.min.js" integrity="sha384-vBWWzlZJ8ea9aCX4pEW3rVHjgjt7zpkNpZk+02D9phzyeVkE+jo0ieGizqPLForn" crossorigin="anonymous"></script>
  </body>
</html>
