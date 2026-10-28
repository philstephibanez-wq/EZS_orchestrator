<?php
declare(strict_types=1);

namespace Ezs\Web\Module\Coordination\Controller;

use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Attribute\Route;
use Twig\Environment;

final class JobsPageController
{
    #[Route('/jobs', name: 'ezs_v2_jobs_page', methods: ['GET'])]
    public function index(Environment $twig): Response
    {
        return new Response($twig->render('jobs/index.html.twig'), 200, [
            'Content-Type' => 'text/html; charset=UTF-8',
            'Cache-Control' => 'no-store',
        ]);
    }
}
