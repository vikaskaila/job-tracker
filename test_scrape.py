from jobspy import scrape_jobs
import pandas as pd

print("Testing JobSpy description extraction...")
print("=" * 80)

# Test with the same search term
jobs = scrape_jobs(
    search_term='Quality Management',
    site_name=['indeed', 'linkedin'],
    location='Hamburg',
    results_wanted=5
)

print(f'\nTotal jobs returned: {len(jobs)}')
print(f'Available columns: {list(jobs.columns)}')
print("\n" + "=" * 80)

print('\nSample jobs from JobSpy:')
for idx, (_, job) in enumerate(jobs.iterrows()):
    print(f'\n[Job {idx+1}]')
    print(f'  Title: {job["title"][:60]}...')
    print(f'  Company: {job["company"]}')
    print(f'  Site: {job["site"]}')
    desc = job.get("description", "")
    if pd.notna(desc) and desc:
        print(f'  Description: {str(desc)[:150]}...')
        print(f'  Description Length: {len(str(desc))}')
    else:
        print(f'  Description: EMPTY (None or empty string)')

print("\n" + "=" * 80)
print("Conclusion: JobSpy is " + ("returning descriptions" if jobs["description"].notna().sum() > 0 else "NOT returning descriptions"))
