#!/usr/bin/env python3
#
# Logs analysis report.  Includes three reports:
#   - Most popular three articles of all time, sorted by number of views
#   - All authors, sorted by number of views on their articles
#   - Days wherein the server had more than 1% errors

import psycopg2

db = psycopg2.connect("dbname=news")
c = db.cursor()

#
# 1. What are the most popular three articles of all time?

popular_articles = '''
select title, count(*) as views
       from log join articles
       on log.path = concat('/article/', articles.slug)
       group by title
       order by views desc
       limit 3;
'''

c.execute(popular_articles)
print("Most popular articles:")
for (title, count) in c.fetchall():
    print("    {} - {} views".format(title, count))
print("-" * 70)

#
# 2. Who are the most popular article authors of all time?

popular_authors = '''
select authors.name, count(*) as views
       from authors, articles, log
       where authors.id = articles.author
         and log.path = concat('/article/', articles.slug)
       group by authors.name
       order by views desc;
'''

c.execute(popular_authors)
print("Most popular authors:")
for (name, count) in c.fetchall():
    print("    {} - {} views".format(name, count))
print("-" * 70)

#
# 3. On which days did more than 1% of requests lead to errors?
#
# There are many ways to do this query!
#
# One approach: Use a single subselect containing two aggregations.
# This query returns a floating-point value that needs to be multiplied
# by 100 to get the percentage.

error_days = '''
select to_char(date, 'FMMonth FMDD, YYYY'), err/total as ratio
       from (select time::date as date,
                    count(*) as total,
                    sum((status != '200 OK')::int)::float as err
                    from log
                    group by date) as errors
       where err/total > 0.01;
'''

# Another approach:  Use a join between two subselects.  This query multiplies
# by 100 in order to avoid doing floating-point math, which also means that
# the answer is already a percentage.
#
# error_days = '''
# select to_char(a.date, 'Mon DD, YYYY'), (a.errors * 100 / b.requests)
#        from (select time::date as date, count(*) as errors
#              from log
#              where status != '200 OK'
#              group by date) as a,
#             (select time::date as date, count(*) as requests
#              from log
#              group by date) as b
#        where a.date = b.date
#        and (a.errors * 100 / b.requests) >= 1
# '''
#
# A third valid approach is to put some or all of the subselect logic into
# a view in the database, and then do a select over this view.

c.execute(error_days)
print("Days with more than 1% errors:")
for (day, err) in c.fetchall():
    pct = err * 100
    print("    {} - {:.2f}% errors".format(day, pct))
