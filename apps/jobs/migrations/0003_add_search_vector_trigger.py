from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('jobs', '0002_remove_job_is_featured_remove_job_salary_negotiable_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE OR REPLACE FUNCTION job_search_vector_update() RETURNS trigger AS $$
                BEGIN
                    NEW.search_vector :=
                        setweight(to_tsvector('simple', coalesce(NEW.title, '')), 'A') ||
                        setweight(to_tsvector('simple', coalesce(NEW.description, '')), 'B') ||
                        setweight(to_tsvector('simple', coalesce(NEW.requirements, '')), 'C') ||
                        setweight(to_tsvector('simple', coalesce(NEW.benefit, '')), 'D');
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;

                CREATE TRIGGER job_search_vector_trigger
                BEFORE INSERT OR UPDATE ON jobs_job
                FOR EACH ROW EXECUTE FUNCTION job_search_vector_update();
            """,
            reverse_sql="""
                DROP TRIGGER IF EXISTS job_search_vector_trigger ON jobs_job;
                DROP FUNCTION IF EXISTS job_search_vector_update();
            """
        ),
    ]
