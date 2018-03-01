# Logs Analysis

Create first database and populate the DB:
$ sudo -i -u postgres
$ createdb news           <==== it worked this way


## How to run

`python3 logs_analysis.py`

## Discussion of queries

### 1. Most popular articles

```
select title, count(*) as views
       from log join articles
       on log.path = concat('/article/', articles.slug)
       group by title
       order by views desc
       limit 3;
```

What we want to do is display the title and the number of views for each of the
top articles.  The `log` table contains one entry for each page view, but does
not contain the titles; so we need to join with the `articles` table.

Looking at the data, I found out that the `log.path` column matches up with
the `articles.slug` column, but the format is a little different, so I had to
concatenate `'/article/'` to the slug to get the path.


### 2. Most popular author

```
select authors.name, count(*) as views
       from authors, articles, log
       where authors.id = articles.author
         and log.path = concat('/article/', articles.slug)
       group by authors.name
       order by views desc;
```

This is very similar to the first query, only here we're joining over three
tables instead of two.  I switched to the implicit join style for clarity.


### 3. High error rate

```
select to_char(date, 'FMMonth FMDD, YYYY'), err/total as ratio
       from (select time::date as date,
                    count(*) as total,
                    sum((status != '200 OK')::int)::float as err
                    from log
                    group by date) as errors
       where err/total > 0.01;
```

I had to do a bunch of research in the PostgreSQL documentation for this one.

The inner query produces a single row for each date that occurs in the `log`
table.  The columns are the date, the total number of requests on that date,
and the number of errors.

The sum that produces the `err` column is a little bit tricky.  If the status
is _not_ `'200 OK'`, that means the request was an error.  Converting the
boolean to an `int` produces 0 (no error) or 1 (error).  Summing these values
gives us the number of errors on a given date.  I convert this to `float`
so that the division `err/total` will use float division.

The outer query computes the ratio for each date and extracts the entries
where the ratio exceeds 0.01 (1%).

