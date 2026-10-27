<?php

declare(strict_types=1);

namespace Ezs\Web\Module\Infrastructure\Controller;

use Ezs\Web\Module\Infrastructure\EnvironmentCatalog;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Attribute\Route;
use Twig\Environment;

final class HomeController
{
    #[Route('/', name: 'ezs_v2_home', methods: ['GET'])]
    public function index(Environment $twig, EnvironmentCatalog $catalog): Response
    {
        return new Response($twig->render('infrastructure/index.html.twig', ['environments' => $catalog->all()]));
    }
}
